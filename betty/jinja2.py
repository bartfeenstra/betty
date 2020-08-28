import asyncio
import datetime
import json as stdjson
import os
import re
from contextlib import suppress
from itertools import takewhile
from os.path import join, exists
from typing import Union, Dict, Type, Optional, Callable, Iterable
from urllib.parse import urlparse

from PIL import Image
from babel import Locale
from geopy import units
from geopy.format import DEGREES_FORMAT
from jinja2 import Environment, select_autoescape, evalcontextfilter, escape, FileSystemLoader, contextfilter
from jinja2.asyncsupport import auto_await
from jinja2.filters import prepare_map, make_attrgetter
from jinja2.runtime import Macro, resolve_or_missing, StrictUndefined
from jinja2.utils import htmlsafe_json_dumps, Namespace as Jinja2Namespace
from markupsafe import Markup
from resizeimage import resizeimage

from betty.ancestry import File, Citation, Identifiable, Resource, HasLinks, HasFiles, Subject, Witness, Dated, \
    RESOURCE_TYPES
from betty.config import Configuration
from betty.fs import makedirs, hashfile, is_hidden, iterfiles
from betty.functools import walk, asynciter
from betty.importlib import import_any
from betty.json import JSONEncoder
from betty.locale import negotiate_localizeds, Localized, format_datey, Datey, negotiate_locale, Date, DateRange
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


class HtmlProvider:
    """
    @todo This class has nothing to do with Jinja2, but placing it in the render module causes a circular dependency.
    """

    @property
    def css_paths(self) -> Iterable[str]:
        return []

    @property
    def js_paths(self) -> Iterable[str]:
        return []


class Namespace(Jinja2Namespace):
    def __getattribute__(self, item):
        # Fix https://github.com/pallets/jinja/issues/1180.
        if '__class__' == item:
            return object.__getattribute__(self, item)
        return Jinja2Namespace.__getattribute__(self, item)


def create_environment(site: Site) -> Environment:
    template_directory_paths = list(
        [join(path, 'templates') for path in site.assets.paths])
    environment = Environment(
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
    if site.configuration.mode == 'development':
        environment.add_extension('jinja2.ext.debug')

    def _gettext(*args, **kwargs):
        return gettext(*args, **kwargs)

    def _ngettext(*args, **kwargs):
        return ngettext(*args, **kwargs)
    environment.install_gettext_callables(_gettext, _ngettext)
    environment.policies['ext.i18n.trimmed'] = True
    # Fix https://github.com/pallets/jinja/issues/1180.
    environment.globals['namespace'] = Namespace
    environment.globals['site'] = site
    environment.globals['locale'] = site.locale
    today = datetime.date.today()
    current_date = Date(today.year, today.month, today.day)
    environment.globals['current_date'] = current_date
    environment.globals['plugins'] = _Plugins(site.plugins)
    environment.globals['urlparse'] = urlparse
    environment.filters['map'] = _filter_map
    environment.filters['flatten'] = _filter_flatten
    environment.filters['walk'] = _filter_walk
    environment.filters['takewhile'] = _filter_takewhile
    environment.filters['locale_get_data'] = lambda locale: Locale.parse(
        locale, '-')
    environment.filters['negotiate_localizeds'] = _filter_negotiate_localizeds
    environment.filters['sort_localizeds'] = _filter_sort_localizeds
    environment.filters['select_localizeds'] = _filter_select_localizeds
    environment.filters['negotiate_dateds'] = _filter_negotiate_dateds
    environment.filters['select_dateds'] = _filter_select_dateds

    # A filter to convert any value to JSON.
    @contextfilter
    def _filter_json(context, data, indent=None):
        return stdjson.dumps(data, indent=indent,
                             cls=JSONEncoder.get_factory(site, resolve_or_missing(context, 'locale')))

    environment.filters['json'] = _filter_json

    # Override Jinja2's built-in JSON filter, which escapes the JSON for use in HTML, to use Betty's own encoder.
    @contextfilter
    def _filter_tojson(context, data, indent=None):
        return htmlsafe_json_dumps(data, indent=indent, dumper=lambda *args, **kwargs: _filter_json(context, *args, **kwargs))

    environment.filters['tojson'] = _filter_tojson
    environment.tests['resource'] = lambda x: isinstance(x, Resource)
    environment.tests['identifiable'] = lambda x: isinstance(x, Identifiable)
    environment.tests['has_links'] = lambda x: isinstance(x, HasLinks)
    environment.tests['has_files'] = lambda x: isinstance(x, HasFiles)
    environment.tests['startswith'] = str.startswith
    environment.tests['subject_role'] = lambda x: isinstance(x, Subject)
    environment.tests['witness_role'] = lambda x: isinstance(x, Witness)
    environment.tests['date_range'] = lambda x: isinstance(x, DateRange)
    for resource_type in RESOURCE_TYPES:
        environment.tests['%s_resource' % resource_type.resource_type_name] = lambda x: isinstance(x, Witness)
    environment.filters['paragraphs'] = _filter_paragraphs

    @contextfilter
    def _filter_format_date(context, date: Datey):
        locale = resolve_or_missing(context, 'locale')
        return format_datey(date, locale)
    environment.filters['format_date'] = _filter_format_date
    environment.filters['format_degrees'] = _filter_format_degrees
    environment.globals['citer'] = _Citer()

    @contextfilter
    def _filter_url(context, resource, media_type=None, locale=None, **kwargs):
        media_type = media_type if media_type else 'text/html'
        locale = locale if locale else resolve_or_missing(context, 'locale')
        return site.localized_url_generator.generate(resource, media_type, locale=locale, **kwargs)

    environment.filters['url'] = _filter_url
    environment.filters['static_url'] = site.static_url_generator.generate
    environment.filters['file'] = lambda *args: _filter_file(site, *args)
    environment.filters['image'] = lambda *args, **kwargs: _filter_image(
        site, *args, **kwargs)
    environment.globals['search_index'] = lambda: Index(site).build()
    environment.globals['html_providers'] = list([plugin for plugin in site.plugins.values() if isinstance(plugin, HtmlProvider)])
    environment.globals['path'] = os.path
    for plugin in site.plugins.values():
        if isinstance(plugin, Jinja2Provider):
            environment.globals.update(plugin.globals)
            environment.filters.update(plugin.filters)
    return environment


class Jinja2Renderer(Renderer):
    def __init__(self, environment: Environment, configuration: Configuration):
        self._environment = environment
        self._configuration = configuration

    async def render_file(self, file_path: str) -> None:
        if not file_path.endswith('.j2'):
            return
        file_destination_path = file_path[:-3]
        data = {}
        if file_destination_path.startswith(self._configuration.www_directory_path) and not is_hidden(file_destination_path):
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
def _filter_takewhile(context, seq, *args, **kwargs):
    try:
        name = args[0]
        args = args[1:]

        def func(item):
            return context.environment.call_test(name, item, args, kwargs)
    except LookupError:
        func = bool
    if seq:
        yield from takewhile(func, seq)


def _filter_file(site: Site, file: File) -> str:
    file_directory_path = os.path.join(
        site.configuration.www_directory_path, 'file')

    destination_name = '%s.%s' % (file.id, file.extension)
    destination_path = '/file/%s' % destination_name
    output_destination_path = os.path.join(
        file_directory_path, destination_name)

    if exists(output_destination_path):
        return destination_path

    makedirs(file_directory_path)
    os.link(file.path, output_destination_path)

    return destination_path


def _filter_image(site: Site, file: File, width: Optional[int] = None, height: Optional[int] = None) -> str:
    if width is None and height is None:
        raise ValueError('At least the width or height must be given.')

    with Image.open(file.path) as image:
        if width is not None:
            width = min(width, image.width)
        if height is not None:
            height = min(height, image.height)

        if width is None:
            size = height
            suffix = '-x%d'
            convert = resizeimage.resize_height
        elif height is None:
            size = width
            suffix = '%dx-'
            convert = resizeimage.resize_width
        else:
            size = (width, height)
            suffix = '%dx%d'
            convert = resizeimage.resize_cover

        file_directory_path = os.path.join(
            site.configuration.www_directory_path, 'file')
        destination_name = '%s-%s.%s' % (file.id, suffix %
                                         size, file.extension)
        destination_path = '/file/%s' % destination_name
        cache_directory_path = join(
            site.configuration.cache_directory_path, 'image')
        cache_file_path = join(cache_directory_path, '%s-%s' %
                               (hashfile(file.path), destination_name))
        output_file_path = join(file_directory_path, destination_name)

        try:
            os.link(cache_file_path, output_file_path)
        except FileExistsError:
            pass
        except FileNotFoundError:
            if exists(output_file_path):
                return destination_path
            makedirs(cache_directory_path)
            convert(image, size).save(cache_file_path)
            makedirs(file_directory_path)
            os.link(cache_file_path, output_file_path)

    return destination_path


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
        date = resolve_or_missing(context, 'current_date')
    return filter(lambda dated: dated.date is None or dated.date.comparable and dated.date in date, dateds)
