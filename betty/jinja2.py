import asyncio
import datetime
import json as stdjson
import os
import re
import warnings
from contextlib import suppress
from pathlib import Path
from typing import Dict, Callable, Iterable, Type, Optional, Any, Union, Iterator, AsyncIterable, ContextManager, cast, \
    AsyncContextManager

import aiofiles
import pdf2image
from PIL import Image
from PIL.Image import DecompressionBombWarning
from babel import Locale
from geopy import units
from geopy.format import DEGREES_FORMAT
from jinja2 import Environment as Jinja2Environment, select_autoescape, FileSystemLoader, pass_context, pass_eval_context, Template, \
    nodes
from jinja2.ext import Extension
from jinja2.filters import prepare_map, make_attrgetter
from jinja2.nodes import EvalContext
from jinja2.runtime import StrictUndefined, Context, Macro, DebugUndefined
from jinja2.utils import htmlsafe_json_dumps
from markupsafe import Markup, escape
from resizeimage import resizeimage

from betty.app import App
from betty.asyncio import sync
from betty.fs import hashfile, iterfiles, CACHE_DIRECTORY_PATH
from betty.functools import walk
from betty.html import CssProvider, JsProvider
from betty.json import JSONEncoder
from betty.locale import negotiate_localizeds, Localized, format_datey, Datey, negotiate_locale, Date, DateRange
from betty.lock import AcquiredError
from betty.model import Entity, get_entity_type_name, GeneratedEntityId
from betty.model.ancestry import File, Citation, HasLinks, HasFiles, Subject, Witness, Dated
from betty.os import link_or_copy, PathLike
from betty.path import rootname
from betty.project import Configuration
from betty.render import Renderer
from betty.search import Index
from betty.string import camel_case_to_snake_case, camel_case_to_kebab_case, upper_camel_case_to_lower_camel_case


class _Citer:
    def __init__(self):
        self._citations = []

    def __iter__(self) -> Iterable[Citation]:
        return enumerate(self._citations, 1)

    def __len__(self) -> int:
        return len(self._citations)

    def cite(self, citation: Citation) -> int:
        if citation not in self._citations:
            self._citations.append(citation)
        return self._citations.index(citation) + 1

    def track(self) -> None:
        self.clear()

    def clear(self) -> None:
        self._citations = []


class Jinja2Provider:
    @property
    def globals(self) -> Dict[str, Callable]:
        return {}

    @property
    def filters(self) -> Dict[str, Callable]:
        return {}


class _ContextManagerExtension(Extension):
    tags = {'enter'}

    def parse(self, parser):
        lineno = next(parser.stream).lineno
        context = parser.parse_expression()
        body = parser.parse_statements(('name:exit',), drop_needle=True)
        return nodes.CallBlock(
            self.call_method('_enter_context', [context]),
            [],
            [],
            body,
        ).set_lineno(lineno)

    def _enter_context(self, context: ContextManager, caller):
        if hasattr(context, '__aenter__'):
            return self._enter_async_context(cast(AsyncContextManager, context), caller)
        return self._enter_sync_context(context, caller)

    def _enter_sync_context(self, context: ContextManager, caller):
        with context:
            return caller()

    @sync
    async def _enter_async_context(self, context: AsyncContextManager, caller):
        async with context:
            return caller()


class Environment(Jinja2Environment):
    def __init__(self, app: App):
        template_directory_paths = [str(path / 'templates') for path, _ in app.assets.paths]
        super().__init__(loader=FileSystemLoader(template_directory_paths),
                         undefined=DebugUndefined if app.project.configuration.debug else StrictUndefined,
                         autoescape=select_autoescape(['html']),
                         trim_blocks=True,
                         extensions=[
                             'jinja2.ext.do',
                             'jinja2.ext.i18n',
                             'betty.jinja2._ContextManagerExtension',
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
        # Wrap the callables so they always call the built-ins available runtime, because those change when the current
        # locale does.
        self.install_gettext_callables(  # type: ignore
            lambda *args, **kwargs: gettext(*args, **kwargs),
            lambda *args, **kwargs: ngettext(*args, **kwargs),
            pgettext=lambda *args, **kwargs: pgettext(*args, **kwargs),  # type: ignore
            npgettext=lambda *args, **kwargs: npgettext(*args, **kwargs),  # type: ignore
        )
        self.policies['ext.i18n.trimmed'] = True

    def _init_globals(self) -> None:
        self.globals['app'] = self.app
        today = datetime.date.today()
        self.globals['today'] = Date(today.year, today.month, today.day)
        self.globals['citer'] = _Citer()
        self.globals['search_index'] = lambda: Index(self.app).build()
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

    def _init_filters(self) -> None:
        self.filters['unique'] = _filter_unique
        self.filters['map'] = _filter_map
        self.filters['flatten'] = _filter_flatten
        self.filters['walk'] = _filter_walk
        self.filters['locale_get_data'] = lambda locale: Locale.parse(
            locale, '-')
        self.filters['negotiate_localizeds'] = _filter_negotiate_localizeds
        self.filters['sort_localizeds'] = _filter_sort_localizeds
        self.filters['select_localizeds'] = _filter_select_localizeds
        self.filters['negotiate_dateds'] = _filter_negotiate_dateds
        self.filters['select_dateds'] = _filter_select_dateds
        self.filters['json'] = _filter_json
        self.filters['tojson'] = _filter_tojson
        self.filters['paragraphs'] = _filter_paragraphs
        self.filters['format_date'] = _filter_format_date
        self.filters['format_degrees'] = _filter_format_degrees
        self.filters['url'] = _filter_url
        self.filters['static_url'] = self.app.static_url_generator.generate
        self.filters['file'] = lambda *args: _filter_file(self.app, *args)
        self.filters['image'] = lambda *args, **kwargs: _filter_image(self.app, *args, **kwargs)
        self.filters['entity_type_name'] = get_entity_type_name
        self.filters['camel_case_to_snake_case'] = camel_case_to_snake_case
        self.filters['camel_case_to_kebab_case'] = camel_case_to_kebab_case
        self.filters['upper_camel_case_to_lower_camel_case'] = upper_camel_case_to_lower_camel_case

    def _init_tests(self) -> None:
        self.tests['entity'] = lambda x: isinstance(x, Entity)

        def _build_test_entity_type(resource_type: Type[Entity]):
            def _test_resource(x):
                return isinstance(x, resource_type)
            return _test_resource
        for entity_type in self.app.entity_types:
            self.tests[f'{camel_case_to_snake_case(get_entity_type_name(entity_type))}_entity'] = _build_test_entity_type(entity_type)
        self.tests['generated_entity_id'] = lambda x: isinstance(x, Entity) and isinstance(x.id, GeneratedEntityId) or isinstance(x, GeneratedEntityId)
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


Template.environment_class = Environment


class Jinja2Renderer(Renderer):
    def __init__(self, environment: Environment, configuration: Configuration):
        self._environment = environment
        self._configuration = configuration

    async def render_file(self, file_path: PathLike) -> None:
        file_path_str = str(file_path)
        if not file_path_str.endswith('.j2'):
            return
        file_destination_path_str = file_path_str[:-3]
        data = {}
        if file_destination_path_str.startswith(str(self._configuration.www_directory_path)):
            resource = '/'.join(Path(file_destination_path_str[len(str(self._configuration.www_directory_path)):].strip(os.sep)).parts)
            if self._configuration.multilingual:
                resource_parts = resource.lstrip('/').split('/')
                if resource_parts[0] in map(lambda x: x.alias, self._configuration.locales):
                    resource = '/'.join(resource_parts[1:])
            data['page_resource'] = resource
        root_path = rootname(file_path)
        template_name = '/'.join(Path(file_path).relative_to(root_path).parts)
        template = FileSystemLoader(root_path).load(self._environment, template_name, self._environment.globals)
        async with aiofiles.open(file_destination_path_str, 'w', encoding='utf-8') as f:
            await f.write(template.render(data))
        os.remove(file_path)

    async def render_tree(self, tree_path: PathLike) -> None:
        await asyncio.gather(
            *[self.render_file(file_path) async for file_path in iterfiles(tree_path) if str(file_path).endswith('.j2')],
        )


@pass_context
def _filter_url(context: Context, resource: Any, media_type: Optional[str] = None, *args, **kwargs) -> str:
    media_type = 'text/html' if media_type is None else media_type
    return cast(Environment, context.environment).app.url_generator.generate(resource, media_type, *args, **kwargs)


@pass_context
def _filter_json(context: Context, data: Any, indent: Optional[int] = None) -> str:
    """
    Converts a value to a JSON string.
    """
    return stdjson.dumps(data, indent=indent, cls=JSONEncoder.get_factory(context.environment.app))


@pass_context
def _filter_tojson(context: Context, data: Any, indent: Optional[int] = None) -> str:
    """
    Converts a value to a JSON string safe for use in an HTML document.

    This mimics Jinja2's built-in JSON filter, but uses Betty's own JSON encoder.
    """
    return htmlsafe_json_dumps(data, indent=indent, dumps=lambda *args, **kwargs: _filter_json(context, *args, **kwargs))


def _filter_flatten(items: Union[Iterable, Iterable]) -> Iterable:
    for item in items:
        for child in item:
            yield child


def _filter_walk(item: Any, attribute_name: str) -> Iterable[Any]:
    return walk(item, attribute_name)


_paragraph_re = re.compile(r'(?:\r\n|\r|\n){2,}')


@pass_eval_context
def _filter_paragraphs(eval_ctx: EvalContext, text: str) -> Union[str, Markup]:
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
    return DEGREES_FORMAT % format_dict


def _filter_unique(items: Iterable) -> Iterator:
    seen = []
    for item in items:
        if item not in seen:
            yield item
            seen.append(item)


@pass_context
def _filter_map(context: Context, value: Union[AsyncIterable, Iterable], *args: Any, **kwargs: Any,):
    """
    Maps an iterable's values.

    This mimics Jinja2's built-in map filter, but allows macros as callbacks.
    """
    if value:
        if len(args) > 0 and isinstance(args[0], Macro):
            func = args[0]
        else:
            func = prepare_map(context, args, kwargs)
        for item in value:
            yield func(item)


def _filter_file(app: App, file: File) -> str:
    with suppress(AcquiredError):
        app.locks.acquire((_filter_file, file))
        file_destination_path = app.project.configuration.www_directory_path / 'file' / file.id / 'file' / file.path.name
        app.executor.submit(_do_filter_file, file.path, file_destination_path)

    return f'/file/{file.id}/file/{file.path.name}'


def _do_filter_file(file_source_path: Path, file_destination_path: Path) -> None:
    file_destination_path.parent.mkdir(exist_ok=True, parents=True)
    link_or_copy(file_source_path, file_destination_path)


def _filter_image(app: App, file: File, width: Optional[int] = None, height: Optional[int] = None) -> str:
    if width is None and height is None:
        raise ValueError('At least the width or height must be given.')

    destination_name = '%s-' % file.id
    if width is None:
        destination_name += '-x%d' % height
    elif height is None:
        destination_name += '%dx-' % width
    else:
        destination_name += '%dx%d' % (width, height)

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
        app.executor.submit(task, file.path, cache_directory_path, file_directory_path, destination_name, width, height)

    destination_public_path = '/file/%s' % destination_name

    return destination_public_path


def _execute_filter_image_image(file_path: Path, *args, **kwargs) -> None:
    with warnings.catch_warnings():
        # Ignore warnings about decompression bombs, because we know where the files come from.
        warnings.simplefilter('ignore', category=DecompressionBombWarning)
        image = Image.open(file_path)
    try:
        _execute_filter_image(image, file_path, *args, **kwargs)
    finally:
        image.close()


def _execute_filter_image_application_pdf(file_path: Path, *args, **kwargs) -> None:
    with warnings.catch_warnings():
        # Ignore warnings about decompression bombs, because we know where the files come from.
        warnings.simplefilter('ignore', category=DecompressionBombWarning)
        image = pdf2image.convert_from_path(file_path, fmt='jpeg')[0]
    try:
        _execute_filter_image(image, file_path, *args, **kwargs)
    finally:
        image.close()


def _execute_filter_image(image: Image, file_path: Path, cache_directory_path: Path, destination_directory_path: Path, destination_name: str, width: int, height: int) -> None:
    destination_directory_path.mkdir(exist_ok=True, parents=True)
    cache_file_path = cache_directory_path / ('%s-%s' % (hashfile(file_path), destination_name))
    destination_file_path = destination_directory_path / destination_name

    try:
        link_or_copy(cache_file_path, destination_file_path)
    except FileNotFoundError:
        cache_directory_path.mkdir(exist_ok=True, parents=True)
        with image:
            if width is not None:
                width = min(width, image.width)
            if height is not None:
                height = min(height, image.height)

            if width is None:
                size = height
                convert = resizeimage.resize_height
            elif height is None:
                size = width
                convert = resizeimage.resize_width
            else:
                size = (width, height)
                convert = resizeimage.resize_cover
            convert(image, size).save(cache_file_path)
        destination_directory_path.mkdir(exist_ok=True, parents=True)
        link_or_copy(cache_file_path, destination_file_path)


@pass_context
def _filter_negotiate_localizeds(context: Context, localizeds: Iterable[Localized]) -> Optional[Localized]:
    return negotiate_localizeds(context.environment.app.locale, list(localizeds))


@pass_context
def _filter_sort_localizeds(context: Context, localizeds: Iterable[Localized], localized_attribute: str, sort_attribute: str) -> Iterable[Localized]:
    get_localized_attr = make_attrgetter(
        context.environment, localized_attribute)
    get_sort_attr = make_attrgetter(context.environment, sort_attribute)

    def _get_sort_key(x):
        return get_sort_attr(negotiate_localizeds(context.environment.app.locale, get_localized_attr(x)))

    return sorted(localizeds, key=_get_sort_key)


@pass_context
def _filter_select_localizeds(context: Context, localizeds: Iterable[Localized], include_unspecified: bool = False) -> Iterable[Localized]:
    for localized in localizeds:
        if include_unspecified and localized.locale in {None, 'mis', 'mul', 'und', 'zxx'}:
            yield localized
        if localized.locale is not None and negotiate_locale(context.environment.app.locale, [localized.locale]) is not None:
            yield localized


@pass_context
def _filter_negotiate_dateds(context: Context, dateds: Iterable[Dated], date: Optional[Datey]) -> Optional[Dated]:
    with suppress(StopIteration):
        return next(_filter_select_dateds(context, dateds, date))


@pass_context
def _filter_select_dateds(context: Context, dateds: Iterable[Dated], date: Optional[Datey]) -> Iterator[Dated]:
    if date is None:
        date = context.resolve_or_missing('today')
    return filter(lambda dated: dated.date is None or dated.date.comparable and dated.date in date, dateds)


@pass_context
def _filter_format_date(context: Context, date: Datey) -> str:
    return format_datey(date, context.environment.app.locale)
