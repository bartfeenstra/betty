import asyncio
import datetime
import json as stdjson
import os
import re
import warnings
from contextlib import suppress
from os.path import join, relpath
from pathlib import Path
from typing import Union, Dict, Type, Optional, Callable, Iterable, AsyncIterable, Any, Iterator

import pdf2image
from PIL import Image
from PIL.Image import DecompressionBombWarning
from babel import Locale
from geopy import units
from geopy.format import DEGREES_FORMAT
from jinja2 import Environment, select_autoescape, evalcontextfilter, escape, FileSystemLoader, contextfilter, Template
from jinja2.asyncsupport import auto_await
from jinja2.filters import prepare_map, make_attrgetter
from jinja2.nodes import EvalContext
from jinja2.runtime import Macro, resolve_or_missing, StrictUndefined, Context
from jinja2.utils import htmlsafe_json_dumps
from markupsafe import Markup
from resizeimage import resizeimage

from betty.ancestry import File, Citation, Identifiable, Resource, HasLinks, HasFiles, Subject, Witness, Dated, \
    RESOURCE_TYPES
from betty.config import Configuration
from betty.fs import makedirs, hashfile, iterfiles
from betty.functools import walk
from betty.html import HtmlProvider
from betty.importlib import import_any
from betty.json import JSONEncoder
from betty.locale import negotiate_localizeds, Localized, format_datey, Datey, negotiate_locale, Date, DateRange
from betty.lock import AcquiredError
from betty.os import link_or_copy
from betty.path import rootname, extension
from betty.plugin import Plugin
from betty.render import Renderer
from betty.search import Index
from betty.site import Site


class _Plugins:
    def __init__(self, plugins: Dict[Type[Plugin], Plugin]):
        self._plugins = plugins

    def __getitem__(self, plugin_type_name):
        try:
            return self._plugins[import_any(plugin_type_name)]
        except ImportError:
            raise KeyError('Unknown plugin "%s".' % plugin_type_name)

    def __contains__(self, plugin_type_name) -> bool:
        with suppress(ImportError):
            return import_any(plugin_type_name) in self._plugins
        return False


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


class BettyEnvironment(Environment):
    site: Site

    def __init__(self, site: Site):
        template_directory_paths = [join(path, 'templates') for path in site.assets.paths]

        Environment.__init__(self,
                             enable_async=True,
                             loader=FileSystemLoader(template_directory_paths),
                             undefined=StrictUndefined,
                             autoescape=select_autoescape(['html']),
                             trim_blocks=True,
                             extensions=[
                                 'jinja2.ext.do',
                                 'jinja2.ext.i18n',
                             ],
                             )

        self.site = site

        if site.configuration.mode == 'development':
            self.add_extension('jinja2.ext.debug')

        self._init_i18n()
        self._init_globals()
        self._init_filters()
        self._init_tests()
        self._init_plugins()

    def _init_i18n(self) -> None:
        # Wrap the callables so they always call the built-ins available runtime, because those change when the current
        # locale does.
        self.install_gettext_callables(
            lambda *args, **kwargs: gettext(*args, **kwargs),
            lambda *args, **kwargs: ngettext(*args, **kwargs),
        )
        self.policies['ext.i18n.trimmed'] = True

    def _init_globals(self) -> None:
        self.globals['site'] = self.site
        self.globals['locale'] = self.site.locale
        today = datetime.date.today()
        self.globals['today'] = Date(today.year, today.month, today.day)
        self.globals['plugins'] = _Plugins(self.site.plugins)
        self.globals['citer'] = _Citer()
        self.globals['search_index'] = lambda: Index(self.site).build()
        self.globals['html_providers'] = list([plugin for plugin in self.site.plugins.values() if isinstance(plugin, HtmlProvider)])
        self.globals['path'] = os.path

    def _init_filters(self) -> None:
        self.filters['set'] = set
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
        self.filters['static_url'] = self.site.static_url_generator.generate
        self.filters['file'] = lambda *args: _filter_file(self.site, *args)
        self.filters['image'] = lambda *args, **kwargs: _filter_image(self.site, *args, **kwargs)

    def _init_tests(self) -> None:
        self.tests['resource'] = lambda x: isinstance(x, Resource)

        def _build_test_resource_type(resource_type: Type[Resource]):
            def _test_resource(x):
                return isinstance(x, resource_type)
            return _test_resource
        for resource_type in RESOURCE_TYPES:
            self.tests['%s_resource' % resource_type.resource_type_name()] = _build_test_resource_type(resource_type)
        self.tests['identifiable'] = lambda x: isinstance(x, Identifiable)
        self.tests['has_links'] = lambda x: isinstance(x, HasLinks)
        self.tests['has_files'] = lambda x: isinstance(x, HasFiles)
        self.tests['starts_with'] = str.startswith
        self.tests['subject_role'] = lambda x: isinstance(x, Subject)
        self.tests['witness_role'] = lambda x: isinstance(x, Witness)
        self.tests['date_range'] = lambda x: isinstance(x, DateRange)

    def _init_plugins(self) -> None:
        for plugin in self.site.plugins.values():
            if isinstance(plugin, Jinja2Provider):
                self.globals.update(plugin.globals)
                self.filters.update(plugin.filters)


Template.environment_class = BettyEnvironment


class Jinja2Renderer(Renderer):
    def __init__(self, environment: Environment, configuration: Configuration):
        self._environment = environment
        self._configuration = configuration

    async def render_file(self, file_path: str) -> None:
        if not file_path.endswith('.j2'):
            return
        file_destination_path = file_path[:-3]
        data = {}
        if file_destination_path.startswith(self._configuration.www_directory_path):
            resource = '/'.join(Path(file_destination_path[len(self._configuration.www_directory_path):].strip(os.sep)).parts)
            if self._configuration.multilingual:
                resource_parts = resource.lstrip('/').split('/')
                if resource_parts[0] in map(lambda x: x.alias, self._configuration.locales.values()):
                    resource = '/'.join(resource_parts[1:])
            data['page_resource'] = resource
        root_path = rootname(file_path)
        template_name = '/'.join(Path(relpath(file_path, root_path)).parts)
        template = FileSystemLoader(root_path).load(self._environment, template_name, self._environment.globals)
        with open(file_destination_path, 'w') as f:
            f.write(await template.render_async(data))
        os.remove(file_path)

    async def render_tree(self, tree_path: str) -> None:
        await asyncio.gather(
            *[self.render_file(file_path) async for file_path in iterfiles(tree_path) if file_path.endswith('.j2')],
        )


@contextfilter
def _filter_url(context: Context, resource: Any, media_type: Optional[str] = None, locale: Optional[str] = None, **kwargs) -> str:
    media_type = 'text/html' if media_type is None else media_type
    locale = locale if locale else resolve_or_missing(context, 'locale')
    return context.environment.site.localized_url_generator.generate(resource, media_type, locale=locale, **kwargs)


@contextfilter
def _filter_json(context: Context, data: Any, indent: Optional[int] = None) -> str:
    """
    Converts a value to a JSON string.
    """
    return stdjson.dumps(data, indent=indent,
                         cls=JSONEncoder.get_factory(context.environment.site, resolve_or_missing(context, 'locale')))


@contextfilter
def _filter_tojson(context: Context, data: Any, indent: Optional[int] = None) -> str:
    """
    Converts a value to a JSON string safe for use in an HTML document.

    This mimics Jinja2's built-in JSON filter, but uses Betty's own JSON encoder.
    """
    return htmlsafe_json_dumps(data, indent=indent, dumper=lambda *args, **kwargs: _filter_json(context, *args, **kwargs))


async def _filter_flatten(items: Union[Iterable, AsyncIterable]) -> Iterable:
    async for item in _asynciter(items):
        async for child in _asynciter(item):
            yield child


def _filter_walk(item: Any, attribute_name: str) -> Iterable[Any]:
    return walk(item, attribute_name)


_paragraph_re = re.compile(r'(?:\r\n|\r|\n){2,}')


@evalcontextfilter
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


async def _filter_unique(items: Iterable) -> Iterator:
    seen = []
    async for item in _asynciter(items):
        if item not in seen:
            yield item
            seen.append(item)


@contextfilter
async def _filter_map(*args, **kwargs):
    """
    Maps an iterable's values.

    This mimics Jinja2's built-in map filter, but allows macros as callbacks.
    """
    if len(args) == 3 and isinstance(args[2], Macro):
        seq = args[1]
        func = args[2]
    else:
        seq, func = prepare_map(args, kwargs)
    if seq:
        async for item in _asynciter(seq):
            yield await auto_await(func(item))


async def _filter_file(site: Site, file: File) -> str:
    file_directory_path = os.path.join(site.configuration.www_directory_path, 'file')

    destination_name = '%s.%s' % (file.id, file.extension)
    destination_public_path = '/file/%s' % destination_name

    with suppress(AcquiredError):
        site.locks.acquire((_filter_file, file))
        site.executor.submit(_do_filter_file, file.path, file_directory_path, destination_name)

    return destination_public_path


def _do_filter_file(file_path: str, destination_directory_path: str, destination_name: str) -> None:
    makedirs(destination_directory_path)
    destination_file_path = os.path.join(destination_directory_path, destination_name)
    link_or_copy(file_path, destination_file_path)


async def _filter_image(site: Site, file: File, width: Optional[int] = None, height: Optional[int] = None) -> str:
    if width is None and height is None:
        raise ValueError('At least the width or height must be given.')

    destination_name = '%s-' % file.id
    if width is None:
        destination_name += '-x%d' % height
    elif height is None:
        destination_name += '%dx-' % width
    else:
        destination_name += '%dx%d' % (width, height)

    file_directory_path = os.path.join(
        site.configuration.www_directory_path, 'file')

    if file.media_type:
        if file.media_type.type == 'image':
            task = _execute_filter_image_image
            destination_name += '.' + extension(file.path)
        elif file.media_type.type == 'application' and file.media_type.subtype == 'pdf':
            task = _execute_filter_image_application_pdf
            destination_name += '.' + 'jpg'
        else:
            raise ValueError('Cannot convert a file of media type "%s" to an image.' % file.media_type)
    else:
        raise ValueError('Cannot convert a file without a media type to an image.')

    with suppress(AcquiredError):
        site.locks.acquire((_filter_image, file, width, height))
        cache_directory_path = join(site.configuration.cache_directory_path, 'image')
        site.executor.submit(task, file.path, cache_directory_path, file_directory_path, destination_name, width, height)

    destination_public_path = '/file/%s' % destination_name

    return destination_public_path


def _execute_filter_image_image(file_path: str, *args, **kwargs) -> None:
    with warnings.catch_warnings():
        # Ignore warnings about decompression bombs, because we know where the files come from.
        warnings.simplefilter('ignore', category=DecompressionBombWarning)
        image = Image.open(file_path)
    _execute_filter_image(image, file_path, *args, **kwargs)


def _execute_filter_image_application_pdf(file_path: str, *args, **kwargs) -> None:
    with warnings.catch_warnings():
        # Ignore warnings about decompression bombs, because we know where the files come from.
        warnings.simplefilter('ignore', category=DecompressionBombWarning)
        image = pdf2image.convert_from_path(file_path, fmt='jpeg')[0]
    _execute_filter_image(image, file_path, *args, **kwargs)


def _execute_filter_image(image: Image, file_path: str, cache_directory_path: str, destination_directory_path: str, destination_name: str, width: int, height: int) -> None:
    makedirs(destination_directory_path)
    cache_file_path = join(cache_directory_path, '%s-%s' % (hashfile(file_path), destination_name))
    destination_file_path = join(destination_directory_path, destination_name)

    try:
        link_or_copy(cache_file_path, destination_file_path)
    except FileNotFoundError:
        makedirs(cache_directory_path)
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
        makedirs(destination_directory_path)
        link_or_copy(cache_file_path, destination_file_path)


@contextfilter
def _filter_negotiate_localizeds(context: Context, localizeds: Iterable[Localized]) -> Optional[Localized]:
    locale = resolve_or_missing(context, 'locale')
    return negotiate_localizeds(locale, list(localizeds))


@contextfilter
def _filter_sort_localizeds(context: Context, localizeds: Iterable[Localized], localized_attribute: str, sort_attribute: str) -> Iterable[Localized]:
    locale = resolve_or_missing(context, 'locale')
    get_localized_attr = make_attrgetter(
        context.environment, localized_attribute)
    get_sort_attr = make_attrgetter(context.environment, sort_attribute)

    def _get_sort_key(x):
        return get_sort_attr(negotiate_localizeds(locale, get_localized_attr(x)))

    return sorted(localizeds, key=_get_sort_key)


@contextfilter
def _filter_select_localizeds(context: Context, localizeds: Iterable[Localized], include_unspecified: bool = False) -> Iterable[Localized]:
    locale = resolve_or_missing(context, 'locale')
    for localized in localizeds:
        if include_unspecified and localized.locale in {None, 'mis', 'mul', 'und', 'zxx'}:
            yield localized
        if localized.locale is not None and negotiate_locale(locale, [localized.locale]) is not None:
            yield localized


@contextfilter
def _filter_negotiate_dateds(context: Context, dateds: Iterable[Dated], date: Optional[Datey]) -> Optional[Dated]:
    with suppress(StopIteration):
        return next(_filter_select_dateds(context, dateds, date))


@contextfilter
def _filter_select_dateds(context: Context, dateds: Iterable[Dated], date: Optional[Datey]) -> Iterator[Dated]:
    if date is None:
        date = resolve_or_missing(context, 'today')
    return filter(lambda dated: dated.date is None or dated.date.comparable and dated.date in date, dateds)


@contextfilter
def _filter_format_date(context: Context, date: Datey) -> str:
    locale = resolve_or_missing(context, 'locale')
    return format_datey(date, locale)


async def _asynciter(items: Union[Iterable, AsyncIterable]) -> AsyncIterable:
    if hasattr(items, '__aiter__'):
        async for item in items:
            yield item
        return
    for item in items:
        yield item
