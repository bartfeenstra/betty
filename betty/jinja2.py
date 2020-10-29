import asyncio
import datetime
import json as stdjson
import os
import re
from contextlib import suppress
from itertools import takewhile
from os.path import join
from typing import Union, Dict, Type, Optional, Callable, Iterable
from urllib.parse import urlparse

import pdf2image
from PIL import Image
from babel import Locale
from geopy import units
from geopy.format import DEGREES_FORMAT
from jinja2 import Environment, select_autoescape, evalcontextfilter, escape, FileSystemLoader, contextfilter, Template
from jinja2.asyncsupport import auto_await
from jinja2.filters import prepare_map, make_attrgetter
from jinja2.runtime import Macro, resolve_or_missing, StrictUndefined
from jinja2.utils import htmlsafe_json_dumps
from markupsafe import Markup
from resizeimage import resizeimage

from betty.ancestry import File, Citation, Identifiable, Resource, HasLinks, HasFiles, Subject, Witness, Dated, \
    RESOURCE_TYPES
from betty.config import Configuration
from betty.fs import makedirs, hashfile, iterfiles
from betty.functools import walk, asynciter
from betty.html import HtmlProvider
from betty.importlib import import_any
from betty.json import JSONEncoder
from betty.locale import negotiate_localizeds, Localized, format_datey, Datey, negotiate_locale, Date, DateRange
from betty.lock import AcquiredError
from betty.media_type import MediaType
from betty.path import extension
from betty.plugin import Plugin
from betty.render import Renderer
from betty.search import Index
from betty.site import Site

_root_loader = FileSystemLoader('/')


class _Plugins:
    def __init__(self, plugins: Dict[Type, Plugin]):
        self._plugins = plugins

    def __getitem__(self, plugin_type_name):
        return self._plugins[import_any(plugin_type_name)]

    def __contains__(self, plugin_type_name):
        try:
            return import_any(plugin_type_name) in self._plugins
        except ImportError:
            return False


class _Citer:
    def __init__(self):
        self._citations = []

    def __iter__(self):
        return enumerate(self._citations, 1)

    def __len__(self):
        return len(self._citations)

    def cite(self, citation: Citation) -> int:
        if citation not in self._citations:
            self._citations.append(citation)
        return self._citations.index(citation) + 1

    def track(self):
        self.clear()

    def clear(self):
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

        def _gettext(*args, **kwargs):
            return gettext(*args, **kwargs)

        def _ngettext(*args, **kwargs):
            return ngettext(*args, **kwargs)
        self.install_gettext_callables(_gettext, _ngettext)
        self.policies['ext.i18n.trimmed'] = True
        self.globals['site'] = site
        self.globals['locale'] = site.locale
        today = datetime.date.today()
        self.globals['today'] = Date(today.year, today.month, today.day)
        self.globals['plugins'] = _Plugins(site.plugins)
        self.globals['parse_url'] = urlparse
        self.filters['parse_media_type'] = MediaType.from_string
        self.filters['set'] = set
        self.filters['map'] = _filter_map
        self.filters['flatten'] = _filter_flatten
        self.filters['walk'] = _filter_walk
        self.filters['selectwhile'] = _filter_selectwhile
        self.filters['locale_get_data'] = lambda locale: Locale.parse(
            locale, '-')
        self.filters['negotiate_localizeds'] = _filter_negotiate_localizeds
        self.filters['sort_localizeds'] = _filter_sort_localizeds
        self.filters['select_localizeds'] = _filter_select_localizeds
        self.filters['negotiate_dateds'] = _filter_negotiate_dateds
        self.filters['select_dateds'] = _filter_select_dateds

        # A filter to convert any value to JSON.
        @contextfilter
        def _filter_json(context, data, indent=None):
            return stdjson.dumps(data, indent=indent,
                                 cls=JSONEncoder.get_factory(site, resolve_or_missing(context, 'locale')))

        self.filters['json'] = _filter_json

        # Override Jinja2's built-in JSON filter, which escapes the JSON for use in HTML, to use Betty's own encoder.
        @contextfilter
        def _filter_tojson(context, data, indent=None):
            return htmlsafe_json_dumps(data, indent=indent, dumper=lambda *args, **kwargs: _filter_json(context, *args, **kwargs))

        self.filters['tojson'] = _filter_tojson
        self.tests['resource'] = lambda x: isinstance(x, Resource)

        def _build_test_resource_type(resource_type: Type[Resource]):
            def _test_resource(x):
                return isinstance(x, resource_type)
            return _test_resource
        for resource_type in RESOURCE_TYPES:
            self.tests['%s_resource' % resource_type.resource_type_name] = _build_test_resource_type(resource_type)
        self.tests['identifiable'] = lambda x: isinstance(x, Identifiable)
        self.tests['has_links'] = lambda x: isinstance(x, HasLinks)
        self.tests['has_files'] = lambda x: isinstance(x, HasFiles)
        self.tests['startswith'] = str.startswith
        self.tests['subject_role'] = lambda x: isinstance(x, Subject)
        self.tests['witness_role'] = lambda x: isinstance(x, Witness)
        self.tests['date_range'] = lambda x: isinstance(x, DateRange)
        self.filters['paragraphs'] = _filter_paragraphs

        @contextfilter
        def _filter_format_date(context, date: Datey):
            locale = resolve_or_missing(context, 'locale')
            return format_datey(date, locale)
        self.filters['format_date'] = _filter_format_date
        self.filters['format_degrees'] = _filter_format_degrees
        self.globals['citer'] = _Citer()

        @contextfilter
        def _filter_url(context, resource, media_type=None, locale=None, **kwargs):
            media_type = media_type if media_type else 'text/html'
            locale = locale if locale else resolve_or_missing(context, 'locale')
            return site.localized_url_generator.generate(resource, media_type, locale=locale, **kwargs)

        self.filters['url'] = _filter_url
        self.filters['static_url'] = site.static_url_generator.generate
        self.filters['file'] = lambda *args: _filter_file(site, *args)
        self.filters['image'] = lambda *args, **kwargs: _filter_image(
            site, *args, **kwargs)
        self.globals['search_index'] = lambda: Index(site).build()
        self.globals['html_providers'] = list([plugin for plugin in site.plugins.values() if isinstance(plugin, HtmlProvider)])
        self.globals['path'] = os.path
        for plugin in site.plugins.values():
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
            # Unix-style paths use forward slashes, so they are valid URL paths.
            resource = file_destination_path[len(
                self._configuration.www_directory_path):]
            if self._configuration.multilingual:
                resource_parts = resource.lstrip('/').split('/')
                if resource_parts[0] in map(lambda x: x.alias, self._configuration.locales.values()):
                    resource = '/'.join(resource_parts[1:])
            data['page_resource'] = resource
        template = _root_loader.load(self._environment, file_path, self._environment.globals)
        with open(file_destination_path, 'w') as f:
            f.write(await template.render_async(data))
        os.remove(file_path)

    async def render_tree(self, tree_path: str) -> None:
        await asyncio.gather(
            *[self.render_file(file_path) async for file_path in iterfiles(tree_path) if file_path.endswith('.j2')],
        )


async def _filter_flatten(items):
    async for item in asynciter(items):
        async for child in asynciter(item):
            yield child


def _filter_walk(item, attribute_name):
    return walk(item, attribute_name)


_paragraph_re = re.compile(r'(?:\r\n|\r|\n){2,}')


@evalcontextfilter
def _filter_paragraphs(eval_ctx, text: str) -> Union[str, Markup]:
    """Converts newlines to <p> and <br> tags.

    Taken from http://jinja.pocoo.org/docs/2.10/api/#custom-filters."""
    result = u'\n\n'.join(u'<p>%s</p>' % p.replace('\n', Markup('<br>\n'))
                          for p in _paragraph_re.split(escape(text)))
    if eval_ctx.autoescape:
        result = Markup(result)
    return result


def _filter_format_degrees(degrees):
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


@contextfilter
async def _filter_map(*args, **kwargs):
    if len(args) == 3 and isinstance(args[2], Macro):
        seq = args[1]
        func = args[2]
    else:
        seq, func = prepare_map(args, kwargs)
    if seq:
        async for item in asynciter(seq):
            yield await auto_await(func(item))


@contextfilter
def _filter_selectwhile(context, seq, *args, **kwargs):
    try:
        name = args[0]
        args = args[1:]

        def func(item):
            return context.environment.call_test(name, item, args, kwargs)
    except LookupError:
        func = bool
    if seq:
        yield from takewhile(func, seq)


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
    os.link(file_path, destination_file_path)


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
        if file.media_type.startswith('image/'):
            task = _execute_filter_image_image
            destination_name += '.' + extension(file.path)
        elif file.media_type == 'application/pdf':
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
    _execute_filter_image(Image.open(file_path), file_path, *args, **kwargs)


def _execute_filter_image_application_pdf(file_path: str, *args, **kwargs) -> None:
    _execute_filter_image(pdf2image.convert_from_path(file_path, fmt='jpeg')[0], file_path, *args, **kwargs)


def _execute_filter_image(image: Image, file_path: str, cache_directory_path: str, destination_directory_path: str, destination_name: str, width: int, height: int) -> None:
    makedirs(destination_directory_path)
    cache_file_path = join(cache_directory_path, '%s-%s' % (hashfile(file_path), destination_name))
    destination_file_path = join(destination_directory_path, destination_name)

    try:
        os.link(cache_file_path, destination_file_path)
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
        os.link(cache_file_path, destination_file_path)


@contextfilter
def _filter_negotiate_localizeds(context, localizeds: Iterable[Localized]) -> Optional[Localized]:
    locale = resolve_or_missing(context, 'locale')
    return negotiate_localizeds(locale, list(localizeds))


@contextfilter
def _filter_sort_localizeds(context, localizeds: Iterable[Localized], localized_attribute: str, sort_attribute: str) -> Iterable[Localized]:
    locale = resolve_or_missing(context, 'locale')
    get_localized_attr = make_attrgetter(
        context.environment, localized_attribute)
    get_sort_attr = make_attrgetter(context.environment, sort_attribute)

    def _get_sort_key(x):
        return get_sort_attr(negotiate_localizeds(locale, get_localized_attr(x)))

    return sorted(localizeds, key=_get_sort_key)


@contextfilter
def _filter_select_localizeds(context, localizeds: Iterable[Localized]) -> Iterable[Localized]:
    locale = resolve_or_missing(context, 'locale')
    for localized in localizeds:
        if negotiate_locale(locale, [localized.locale]) is not None:
            yield localized


@contextfilter
def _filter_negotiate_dateds(context, dateds: Iterable[Dated], date: Optional[Datey]) -> Optional[Dated]:
    with suppress(StopIteration):
        return next(_filter_select_dateds(context, dateds, date))


@contextfilter
def _filter_select_dateds(context, dateds: Iterable[Dated], date: Optional[Datey]) -> Iterable[Dated]:
    if date is None:
        date = resolve_or_missing(context, 'today')
    return filter(lambda dated: dated.date is None or dated.date.comparable and dated.date in date, dateds)
