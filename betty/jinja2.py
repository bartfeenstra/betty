import json as stdjson
import os
import re
from importlib import import_module
from itertools import takewhile
from os.path import join, exists
from shutil import copy2
from typing import Union, Dict, Type, Optional, Callable, Iterable
from urllib.parse import urlparse

from PIL import Image
from babel import Locale
from geopy import units
from geopy.format import DEGREES_FORMAT
from jinja2 import Environment, select_autoescape, evalcontextfilter, escape, FileSystemLoader, contextfilter
from jinja2.filters import prepare_map, make_attrgetter
from jinja2.runtime import Macro, resolve_or_missing, StrictUndefined
from jinja2.utils import htmlsafe_json_dumps
from markupsafe import Markup
from resizeimage import resizeimage

from betty.ancestry import File, Citation, Event, Presence, Identifiable
from betty.config import Configuration
from betty.fs import iterfiles, makedirs, hashfile, is_hidden
from betty.functools import walk
from betty.json import JSONEncoder
from betty.locale import negotiate_localizeds, Localized, format_datey, Datey, Translations
from betty.plugin import Plugin
from betty.site import Site
from betty.url import SiteUrlGenerator, StaticPathUrlGenerator

_root_loader = FileSystemLoader('/')


class _Plugins:
    def __init__(self, plugins: Dict[Type, Plugin]):
        self._plugins = plugins

    def __getitem__(self, plugin_type_name):
        return self._plugins[self._type(plugin_type_name)]

    def __contains__(self, plugin_type_name):
        try:
            return self._type(plugin_type_name) in self._plugins
        except (ImportError, AttributeError):
            return False

    def _type(self, plugin_type_name: str):
        plugin_module_name, plugin_class_name = plugin_type_name.rsplit('.', 1)
        return getattr(import_module(plugin_module_name), plugin_class_name)


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


def create_environment(site: Site, default_locale: Optional[str] = None) -> Environment:
    if default_locale is None:
        default_locale = site.configuration.default_locale
    url_generator = SiteUrlGenerator(site.configuration)
    template_directory_paths = list(
        [join(path, 'templates') for path in site.resources.paths])
    environment = Environment(
        loader=FileSystemLoader(template_directory_paths),
        undefined=StrictUndefined,
        autoescape=select_autoescape(['html']),
        extensions=[
            'jinja2.ext.do',
            'jinja2.ext.i18n',
        ],
    )
    environment.install_gettext_translations(site.translations[default_locale])
    environment.globals['site'] = site
    environment.globals['locale'] = default_locale
    environment.globals['plugins'] = _Plugins(site.plugins)
    environment.globals['EventType'] = Event.Type
    environment.globals['PresenceRole'] = Presence.Role
    environment.globals['urlparse'] = urlparse
    environment.filters['map'] = _filter_map
    environment.filters['flatten'] = _filter_flatten
    environment.filters['walk'] = _filter_walk
    environment.filters['takewhile'] = _filter_takewhile
    environment.filters['locale_get_data'] = lambda locale: Locale.parse(
        locale, '-')
    environment.filters['negotiate_localizeds'] = lambda localizeds: negotiate_localizeds(
        default_locale, localizeds)
    environment.filters['sort_localizeds'] = contextfilter(
        lambda context, *args, **kwargs: _filter_sort_localizeds(context, default_locale, *args, **kwargs))

    # A filter to convert any value to JSON.
    @contextfilter
    def _filter_json(context, data, indent=None):
        return stdjson.dumps(data, indent=indent,
                             cls=JSONEncoder.get_factory(site.configuration, resolve_or_missing(context, 'locale')))

    environment.filters['json'] = _filter_json

    # Override Jinja2's built-in JSON filter, which escapes the JSON for use in HTML, to use Betty's own encoder.
    @contextfilter
    def _filter_tojson(context, data, indent=None):
        return htmlsafe_json_dumps(data, indent=indent, dumper=lambda *args, **kwargs: _filter_json(context, *args, **kwargs))

    environment.filters['tojson'] = _filter_tojson

    def _is_entity(x):
        return isinstance(x, Identifiable)
    environment.filters['is_entity'] = _is_entity
    environment.tests['is_entity'] = _is_entity

    environment.filters['paragraphs'] = _filter_paragraphs

    def _filter_format_date(date: Datey):
        with Translations(site.translations[default_locale]):
            return format_datey(date, default_locale)
    environment.filters['format_date'] = _filter_format_date
    environment.filters['format_degrees'] = _filter_format_degrees
    environment.globals['citer'] = _Citer()

    def _filter_url(resource, content_type=None, locale=None, **kwargs):
        content_type = content_type if content_type else 'text/html'
        locale = locale if locale else default_locale
        return url_generator.generate(resource, content_type, locale=locale, **kwargs)

    environment.filters['url'] = _filter_url
    environment.filters['static_url'] = StaticPathUrlGenerator(
        site.configuration).generate
    environment.filters['file'] = lambda *args: _filter_file(site, *args)
    environment.filters['image'] = lambda *args, **kwargs: _filter_image(
        site, *args, **kwargs)
    for plugin in site.plugins.values():
        if isinstance(plugin, Jinja2Provider):
            environment.globals.update(plugin.globals)
            environment.filters.update(plugin.filters)
    return environment


def render_tree(path: str, environment: Environment, configuration: Optional[Configuration] = None) -> None:
    for file_source_path in iterfiles(path):
        if file_source_path.endswith('.j2'):
            render_file(file_source_path, environment, configuration)


def render_file(file_source_path: str, environment: Environment, configuration: Optional[Configuration] = None) -> None:
    file_destination_path = file_source_path[:-3]
    data = {}
    if configuration is not None:
        if file_destination_path.startswith(configuration.www_directory_path) and not is_hidden(file_destination_path):
            # Unix-style paths use forward slashes, so they are valid URL paths.
            resource = file_destination_path[len(
                configuration.www_directory_path):]
            if configuration.multilingual:
                resource_parts = resource.lstrip('/').split('/')
                if resource_parts[0] in map(lambda x: x.alias, configuration.locales.values()):
                    resource = '/'.join(resource_parts[1:])
            data['resource'] = resource
    template = _root_loader.load(
        environment, file_source_path, environment.globals)
    with open(file_destination_path, 'w') as f:
        f.write(template.render(data))
    os.remove(file_source_path)


def _filter_flatten(items):
    for item in items:
        for child in item:
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
def _filter_map(*args, **kwargs):
    if len(args) == 3 and isinstance(args[2], Macro):
        seq = args[1]
        func = args[2]
    else:
        seq, func = prepare_map(args, kwargs)
    if seq:
        for item in seq:
            yield func(item)


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
    copy2(file.path, output_destination_path)

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
            copy2(cache_file_path, output_file_path)
        except FileNotFoundError:
            if exists(output_file_path):
                return destination_path
            makedirs(cache_directory_path)
            convert(image, size).save(cache_file_path)
            makedirs(file_directory_path)
            copy2(cache_file_path, output_file_path)

    return destination_path


def _filter_sort_localizeds(context, preferred_locale: str, localizeds: Iterable[Localized], localized_attribute: str,
                            sort_attribute: str):
    get_localized_attr = make_attrgetter(
        context.environment, localized_attribute)
    get_sort_attr = make_attrgetter(context.environment, sort_attribute)

    def get_sort_key(x):
        return get_sort_attr(negotiate_localizeds(preferred_locale, get_localized_attr(x)))

    return sorted(localizeds, key=get_sort_key)
