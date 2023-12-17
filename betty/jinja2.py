from __future__ import annotations

import datetime
import json as stdjson
import os
import re
import warnings
from collections import defaultdict
from contextlib import suppress
from pathlib import Path
from typing import Callable, Iterable, Any, Iterator, cast, \
    MutableMapping, Mapping, TypeVar

import aiofiles
from PIL import Image
from PIL.Image import DecompressionBombWarning
from aiofiles import os as aiofiles_os
from aiofiles.os import makedirs
from geopy import units
from geopy.format import DEGREES_FORMAT
from jinja2 import Environment as Jinja2Environment, select_autoescape, FileSystemLoader, pass_context, \
    pass_eval_context, Template as Jinja2Template, TemplateNotFound, BaseLoader
from jinja2.filters import prepare_map, make_attrgetter
from jinja2.nodes import EvalContext
from jinja2.runtime import StrictUndefined, Context, Macro, DebugUndefined, new_context
from jinja2.utils import htmlsafe_json_dumps
from markupsafe import Markup, escape
from pdf2image.pdf2image import convert_from_path

from betty import _resizeimage
from betty.app import App
from betty.asyncio import wait
from betty.fs import hashfile, CACHE_DIRECTORY_PATH
from betty.functools import walk
from betty.html import CssProvider, JsProvider
from betty.locale import negotiate_localizeds, Localized, Datey, negotiate_locale, Date, DateRange, \
    get_data, Localizer
from betty.lock import AcquiredError
from betty.model import Entity, get_entity_type_name, GeneratedEntityId, UserFacingEntity, get_entity_type, \
    AncestryEntityId
from betty.model.ancestry import File, Citation, HasLinks, HasFiles, Subject, Witness, Dated, is_private, is_public, \
    AnonymousCitation, AnonymousSource
from betty.os import link_or_copy
from betty.path import rootname
from betty.project import ProjectConfiguration
from betty.render import Renderer
from betty.serde.dump import Dumpable, DictDump, VoidableDump, Void, minimize, none_void, void_none, Dump
from betty.string import camel_case_to_snake_case, camel_case_to_kebab_case, upper_camel_case_to_lower_camel_case

T = TypeVar('T')


class _Citer:
    def __init__(self, localizer: Localizer):
        self._localizer = localizer
        self._citations: list[Citation] = []
        self._anonymous_source = AnonymousSource(localizer=localizer)
        self._anonymous_citations: dict[AncestryEntityId | None, Citation] = {}

    def __iter__(self) -> enumerate[Citation]:
        return enumerate(self._citations, 1)

    def __len__(self) -> int:
        return len(self._citations)

    def cite(self, citation: Citation) -> int:
        if citation.private:
            source_key = None if citation.source is None else citation.source.ancestry_id
            try:
                citation = self._anonymous_citations[source_key]
            except KeyError:
                citation = AnonymousCitation(
                    source=citation.source or self._anonymous_source,
                    localizer=self._localizer,
                )
                self._anonymous_citations[source_key] = citation
        if citation not in self._citations:
            self._citations.append(citation)
        return self._citations.index(citation) + 1


class _Breadcrumb(Dumpable):
    def __init__(self, label: str, url: str):
        self._label = label
        self._url = url

    def dump(self) -> DictDump[Dump]:
        return {
            '@type': 'ListItem',
            'name': self._label,
            'item': self._url,
        }


class _Breadcrumbs(Dumpable):
    def __init__(self):
        self._breadcrumbs: list[_Breadcrumb] = []

    def append(self, label: str, url: str) -> None:
        self._breadcrumbs.append(_Breadcrumb(label, url))

    def dump(self) -> VoidableDump:
        if not self._breadcrumbs:
            return Void
        return {
            '@context': 'https://schema.org',
            '@type': 'BreadcrumbList',
            'itemListElement': [
                {
                    'position': position,
                    **breadcrumb.dump(),
                }
                for position, breadcrumb
                in enumerate(self._breadcrumbs, 1)
            ],
        }


class EntityContexts:
    def __init__(self, *entities: Entity) -> None:
        self._contexts: dict[type[Entity], Entity | None] = defaultdict(lambda: None)
        for entity in entities:
            self._contexts[entity.type] = entity

    def __getitem__(self, entity_type_or_type_name: type[Entity] | str) -> Entity | None:
        if isinstance(entity_type_or_type_name, str):
            entity_type = get_entity_type(entity_type_or_type_name)
        else:
            entity_type = entity_type_or_type_name
        return self._contexts[entity_type]

    def __call__(self, *entities: Entity) -> EntityContexts:
        updated_contexts = EntityContexts()
        for entity in entities:
            updated_contexts._contexts[entity.type] = entity
        return updated_contexts


class Jinja2Provider:
    @property
    def globals(self) -> dict[str, Any]:
        return {}

    @property
    def filters(self) -> dict[str, Callable[..., Any]]:
        return {}

    @property
    def tests(self) -> dict[str, Callable[..., bool]]:
        return {}


class Template(Jinja2Template):
    environment: Environment

    def new_context(
        self,
        vars: dict[str, Any] | None = None,
        shared: bool = False,
        locals: Mapping[str, Any] | None = None,
    ) -> Context:
        return new_context(
            self.environment,
            self.name,
            self.blocks,
            vars,
            shared,
            {
                'citer': _Citer(self.environment.app.localizer),
                'breadcrumbs': _Breadcrumbs(),
                **self.globals,
            },
            locals,
        )


class Environment(Jinja2Environment):
    template_class = Template
    globals: dict[str, Any]
    filters: dict[str, Callable[..., Any]]
    tests: dict[str, Callable[..., bool]]

    def __init__(self, app: App):
        template_directory_paths = [str(path / 'templates') for path, _ in app.assets.paths]
        super().__init__(loader=FileSystemLoader(template_directory_paths),
                         undefined=DebugUndefined if app.project.configuration.debug else StrictUndefined,
                         autoescape=select_autoescape(['html.j2']),
                         trim_blocks=True,
                         extensions=[
                             'jinja2.ext.do',
                             'jinja2.ext.i18n',
        ],
        )

        self.app = app

        if app.project.configuration.debug:
            self.add_extension('jinja2.ext.debug')

        self._init_i18n()
        self._init_globals()
        self._init_filters()
        self._init_tests()
        self._init_extensions()

    def _init_i18n(self) -> None:
        self.install_gettext_callables(  # type: ignore[attr-defined]
            self.app.localizer.gettext,
            self.app.localizer.ngettext,
            pgettext=self.app.localizer.pgettext,
            npgettext=self.app.localizer.npgettext,
        )
        self.policies['ext.i18n.trimmed'] = True

    def _init_globals(self) -> None:
        self.globals['app'] = self.app
        today = datetime.date.today()
        self.globals['today'] = Date(today.year, today.month, today.day)
        # Ideally we would use the Dispatcher for this. However, it is asynchronous only.
        self.globals['public_css_paths'] = [
            path
            for extension in self.app.extensions.flatten()
            if isinstance(extension, CssProvider)
            for path in extension.public_css_paths
        ]
        self.globals['public_js_paths'] = [
            path
            for extension in self.app.extensions.flatten()
            if isinstance(extension, JsProvider)
            for path in extension.public_js_paths
        ]
        self.globals['path'] = os.path
        self.globals['entity_contexts'] = EntityContexts()

    def _init_filters(self) -> None:
        self.filters['unique'] = _filter_unique
        self.filters['map'] = _filter_map
        self.filters['flatten'] = _filter_flatten
        self.filters['walk'] = _filter_walk
        self.filters['locale_get_data'] = get_data
        self.filters['negotiate_localizeds'] = _filter_negotiate_localizeds
        self.filters['sort_localizeds'] = _filter_sort_localizeds
        self.filters['select_localizeds'] = _filter_select_localizeds
        self.filters['negotiate_dateds'] = _filter_negotiate_dateds
        self.filters['select_dateds'] = _filter_select_dateds
        self.filters['json'] = _filter_json
        self.filters['tojson'] = _filter_tojson
        self.filters['paragraphs'] = _filter_paragraphs
        self.filters['format_datey'] = self.app.localizer.format_datey
        self.filters['format_degrees'] = _filter_format_degrees
        self.filters['url'] = _filter_url
        self.filters['static_url'] = self.app.static_url_generator.generate
        self.filters['file'] = lambda *args: _filter_file(self.app, *args)
        self.filters['image'] = lambda *args, **kwargs: _filter_image(self.app, *args, **kwargs)
        self.filters['entity_type_name'] = get_entity_type_name
        self.filters['camel_case_to_snake_case'] = camel_case_to_snake_case
        self.filters['camel_case_to_kebab_case'] = camel_case_to_kebab_case
        self.filters['upper_camel_case_to_lower_camel_case'] = upper_camel_case_to_lower_camel_case
        self.filters['void_none'] = void_none
        self.filters['none_void'] = none_void
        self.filters['minimize'] = minimize

    def _init_tests(self) -> None:
        self.tests['entity'] = lambda x: isinstance(x, Entity)
        self.tests['public'] = is_public
        self.tests['private'] = is_private
        self.tests['user_facing_entity'] = lambda x: isinstance(x, UserFacingEntity)

        def _build_test_entity_type(resource_type: type[Entity]) -> Callable[[Any], bool]:
            def _test_entity_type(x: Any) -> bool:
                return isinstance(x, resource_type)
            return _test_entity_type
        for entity_type in self.app.entity_types:
            self.tests[f'{camel_case_to_snake_case(get_entity_type_name(entity_type))}_entity'] = _build_test_entity_type(entity_type)
        self.tests['has_generated_entity_id'] = lambda x: isinstance(x, Entity) and isinstance(x.id, GeneratedEntityId) or isinstance(x, GeneratedEntityId)
        self.tests['has_links'] = lambda x: isinstance(x, HasLinks)
        self.tests['has_files'] = lambda x: isinstance(x, HasFiles)
        self.tests['starts_with'] = str.startswith
        self.tests['subject_role'] = lambda x: isinstance(x, Subject)
        self.tests['witness_role'] = lambda x: isinstance(x, Witness)
        self.tests['date_range'] = lambda x: isinstance(x, DateRange)

    def _init_extensions(self) -> None:
        for extension in self.app.extensions.flatten():
            if isinstance(extension, Jinja2Provider):
                self.globals.update(extension.globals)
                self.filters.update(extension.filters)
                self.tests.update(extension.tests)

    def negotiate_template(
        self,
        names: list[str],
        parent: str | None = None,
        globals: MutableMapping[str, Any] | None = None,
    ) -> Template:
        for name in names:
            with suppress(TemplateNotFound):
                return cast(Template, self.get_template(name, parent, globals))
        raise TemplateNotFound(names[-1], f'Cannot find any of the following templates: {", ".join(names)}.')


Template.environment_class = Environment


class Jinja2Renderer(Renderer):
    def __init__(self, environment: Environment, configuration: ProjectConfiguration):
        self._environment = environment
        self._configuration = configuration
        self._loaders: dict[Path, BaseLoader] = {}

    def get_loader(self, root_path: Path) -> BaseLoader:
        if root_path not in self._loaders:
            self._loaders[root_path] = FileSystemLoader(root_path)
        return self._loaders[root_path]

    @property
    def file_extensions(self) -> set[str]:
        return {'.j2'}

    async def render_file(self, file_path: Path) -> Path:
        file_destination_path = file_path.parent / file_path.stem
        data = {}
        try:
            relative_file_destination_path = file_destination_path.relative_to(self._configuration.www_directory_path)
        except ValueError:
            pass
        else:
            resource = '/'.join(relative_file_destination_path.parts)
            if self._configuration.multilingual:
                resource_parts = resource.lstrip('/').split('/')
                if resource_parts[0] in map(lambda x: x.alias, self._configuration.locales.values()):
                    resource = '/'.join(resource_parts[1:])
            data['page_resource'] = resource
        root_path = rootname(file_path)
        rendered = self.get_loader(root_path).load(
            self._environment,
            '/'.join(Path(file_path).relative_to(root_path).parts),
            self._environment.globals,
        ).render(data)
        async with aiofiles.open(file_destination_path, 'w', encoding='utf-8') as f:
            await f.write(rendered)
        await aiofiles_os.remove(file_path)
        return file_destination_path


@pass_context
def _filter_url(context: Context, resource: Any, media_type: str | None = None, *args: Any, **kwargs: Any) -> str:
    return cast(Environment, context.environment).app.url_generator.generate(
        resource,
        media_type or 'text/html',
        *args,
        **kwargs,
    )


@pass_context
def _filter_json(context: Context, data: Any, indent: int | None = None) -> str:
    """
    Converts a value to a JSON string.
    """
    return stdjson.dumps(data, indent=indent, cls=(cast(Environment, context.environment).app.json_encoder))


@pass_context
def _filter_tojson(context: Context, data: Any, indent: int | None = None) -> str:
    """
    Converts a value to a JSON string safe for use in an HTML document.

    This mimics Jinja2's built-in JSON filter, but uses Betty's own JSON encoder.
    """
    return htmlsafe_json_dumps(data, indent=indent, dumps=lambda *args, **kwargs: _filter_json(context, *args, **kwargs))


def _filter_flatten(items: Iterable[Iterable[T]]) -> Iterator[T]:
    for item in items:
        for child in item:
            yield child


def _filter_walk(item: Any, attribute_name: str) -> Iterable[Any]:
    return walk(item, attribute_name)


_paragraph_re = re.compile(r'(?:\r\n|\r|\n){2,}')


@pass_eval_context
def _filter_paragraphs(eval_ctx: EvalContext, text: str) -> str | Markup:
    """Converts newlines to <p> and <br> tags.

    Taken from http://jinja.pocoo.org/docs/2.10/api/#custom-filters."""
    result = u'\n\n'.join(u'<p>%s</p>' % p.replace('\n', Markup('<br>\n'))
                          for p in _paragraph_re.split(escape(text)))
    if eval_ctx.autoescape:
        result = Markup(result)
    return result


def _filter_format_degrees(degrees: int) -> str:
    arcminutes = units.arcminutes(degrees=degrees - int(degrees))
    arcseconds = units.arcseconds(arcminutes=arcminutes - int(arcminutes))
    format_dict = dict(
        deg='°',
        arcmin="'",
        arcsec='"',
        degrees=degrees,
        minutes=round(abs(arcminutes)),
        seconds=round(abs(arcseconds))
    )
    return DEGREES_FORMAT % format_dict  # type: ignore[no-any-return]


def _filter_unique(items: Iterable[T]) -> Iterator[T]:
    seen = []
    for item in items:
        if item not in seen:
            yield item
            seen.append(item)


@pass_context
def _filter_map(context: Context, value: Iterable[Any], *args: Any, **kwargs: Any) -> Any:
    """
    Maps an iterable's values.

    This mimics Jinja2's built-in map filter, but allows macros as callbacks.
    """
    if len(args) > 0 and isinstance(args[0], Macro):
        func: Macro | Callable[[Any], bool] = args[0]
    else:
        func = prepare_map(context, args, kwargs)
    for item in value:
        yield func(item)


def _filter_file(app: App, file: File) -> str:
    with suppress(AcquiredError):
        app.locks.acquire((_filter_file, file))
        file_destination_path = app.project.configuration.www_directory_path / 'file' / file.id / 'file' / file.path.name
        app.delegate_to_thread(lambda: wait(_do_filter_file(file.path, file_destination_path)))

    return f'/file/{file.id}/file/{file.path.name}'


async def _do_filter_file(file_source_path: Path, file_destination_path: Path) -> None:
    await makedirs(file_destination_path.parent, exist_ok=True)
    await link_or_copy(file_source_path, file_destination_path)


def _filter_image(app: App, file: File, width: int | None = None, height: int | None = None) -> str:
    destination_name = '%s-' % file.id
    if height and width:
        destination_name += '%dx%d' % (width, height)
    elif height:
        destination_name += '-x%d' % height
    elif width:
        destination_name += '%dx-' % width
    else:
        raise ValueError('At least the width or height must be given.')

    file_directory_path = app.project.configuration.www_directory_path / 'file'

    if file.media_type:
        if file.media_type.type == 'image':
            task = _execute_filter_image_image
            destination_name += file.path.suffix
        elif file.media_type.type == 'application' and file.media_type.subtype == 'pdf':
            task = _execute_filter_image_application_pdf
            destination_name += '.' + 'jpg'
        else:
            raise ValueError('Cannot convert a file of media type "%s" to an image.' % file.media_type)
    else:
        raise ValueError('Cannot convert a file without a media type to an image.')

    with suppress(AcquiredError):
        app.locks.acquire((_filter_image, file, width, height))
        cache_directory_path = CACHE_DIRECTORY_PATH / 'image'
        app.delegate_to_thread(lambda: wait(task(file.path, cache_directory_path, file_directory_path, destination_name, width, height)))

    destination_public_path = '/file/%s' % destination_name

    return destination_public_path


async def _execute_filter_image_image(file_path: Path, *args: Any, **kwargs: Any) -> None:
    with warnings.catch_warnings():
        # Ignore warnings about decompression bombs, because we know where the files come from.
        warnings.simplefilter('ignore', category=DecompressionBombWarning)
        image = Image.open(file_path)
    try:
        await _execute_filter_image(image, file_path, *args, **kwargs)
    finally:
        image.close()


async def _execute_filter_image_application_pdf(file_path: Path, *args: Any, **kwargs: Any) -> None:
    with warnings.catch_warnings():
        # Ignore warnings about decompression bombs, because we know where the files come from.
        warnings.simplefilter('ignore', category=DecompressionBombWarning)
        image = convert_from_path(file_path, fmt='jpeg')[0]
    try:
        await _execute_filter_image(image, file_path, *args, **kwargs)
    finally:
        image.close()


async def _execute_filter_image(
    image: Image,
    file_path: Path,
    cache_directory_path: Path,
    destination_directory_path: Path,
    destination_name: str,
    width: int | None,
    height: int | None,
) -> None:
    await makedirs(destination_directory_path, exist_ok=True)
    cache_file_path = cache_directory_path / ('%s-%s' % (hashfile(file_path), destination_name))
    destination_file_path = destination_directory_path / destination_name

    try:
        await link_or_copy(cache_file_path, destination_file_path)
    except FileNotFoundError:
        await makedirs(cache_directory_path, exist_ok=True)
        with image:
            if width is not None:
                width = min(width, image.width)
            if height is not None:
                height = min(height, image.height)

            if width is not None and height is not None:
                converted = _resizeimage.resize_cover(image, (width, height))
            elif width is not None:
                converted = _resizeimage.resize_width(image, width)
            elif height is not None:
                converted = _resizeimage.resize_height(image, height)
            else:
                raise ValueError('Width and height cannot both be None.')
            converted.save(cache_file_path)
        await makedirs(destination_directory_path, exist_ok=True)
        await link_or_copy(cache_file_path, destination_file_path)


@pass_context
def _filter_negotiate_localizeds(context: Context, localizeds: Iterable[Localized]) -> Localized | None:
    return negotiate_localizeds(cast(Environment, context.environment).app.locale, list(localizeds))


@pass_context
def _filter_sort_localizeds(context: Context, localizeds: Iterable[Localized], localized_attribute: str, sort_attribute: str) -> Iterable[Localized]:
    get_localized_attr = make_attrgetter(
        context.environment, localized_attribute)
    get_sort_attr = make_attrgetter(context.environment, sort_attribute)

    def _get_sort_key(x: Localized) -> Any:
        return get_sort_attr(negotiate_localizeds(cast(Environment, context.environment).app.locale, get_localized_attr(x)))

    return sorted(localizeds, key=_get_sort_key)


@pass_context
def _filter_select_localizeds(context: Context, localizeds: Iterable[Localized], include_unspecified: bool = False) -> Iterable[Localized]:
    for localized in localizeds:
        if include_unspecified and localized.locale in {None, 'mis', 'mul', 'und', 'zxx'}:
            yield localized
        if localized.locale is not None and negotiate_locale(cast(Environment, context.environment).app.locale, {localized.locale}) is not None:
            yield localized


@pass_context
def _filter_negotiate_dateds(context: Context, dateds: Iterable[Dated], date: Datey | None) -> Dated | None:
    with suppress(StopIteration):
        return next(_filter_select_dateds(context, dateds, date))
    return None


@pass_context
def _filter_select_dateds(context: Context, dateds: Iterable[Dated], date: Datey | None) -> Iterator[Dated]:
    if date is None:
        date = context.resolve_or_missing('today')
    return filter(
        lambda dated: dated.date is None or dated.date.comparable and dated.date in date,
        dateds,
    )
