import calendar
import os
import re
import shutil
from importlib import import_module
from itertools import takewhile
from json import dumps
from os.path import join, splitext
from typing import Iterable, Union, Any, Dict, Type

from geopy import units
from geopy.format import DEGREES_FORMAT
from jinja2 import Environment, select_autoescape, evalcontextfilter, escape, FileSystemLoader, contextfilter
from jinja2.filters import prepare_map
from jinja2.runtime import Macro
from markupsafe import Markup

from betty.ancestry import Entity
from betty.config import Configuration
from betty.event import Event
from betty.fs import makedirs, iterfiles
from betty.functools import walk
from betty.json import JSONEncoder
from betty.plugin import Plugin
from betty.site import Site


class PostRenderEvent(Event):
    def __init__(self, environment: Environment):
        self._environment = environment

    @property
    def environment(self) -> Environment:
        return self._environment


def render(site: Site) -> None:
    template_directory_paths = list([join(path, 'templates') for path in site.resources.paths])
    environment = Environment(
        loader=FileSystemLoader(template_directory_paths),
        autoescape=select_autoescape(['html'])
    )
    environment.globals['site'] = site
    environment.globals['plugins'] = Plugins(site.plugins)
    environment.globals['calendar'] = calendar
    environment.filters['map'] = _render_map
    environment.filters['flatten'] = _render_flatten
    environment.filters['walk'] = _render_walk
    environment.filters['takewhile'] = _render_takewhile
    environment.filters['json'] = _render_json
    environment.filters['paragraphs'] = _render_html_paragraphs
    environment.filters['format_degrees'] = _render_format_degrees
    environment.filters['url'] = lambda *args, **kwargs: _render_url(site.configuration, *args, **kwargs)
    environment.filters['file_url'] = lambda *args, **kwargs: _render_file_url(site.configuration, *args, **kwargs)

    _render_public(site, environment)
    _render_documents(site)
    _render_entity_type(site, environment,
                        site.ancestry.people.values(), 'person')
    _render_entity_type(site, environment,
                        site.ancestry.places.values(), 'place')
    _render_entity_type(site, environment,
                        site.ancestry.events.values(), 'event')
    site.event_dispatcher.dispatch(PostRenderEvent(environment))


def _create_file(path: str) -> object:
    makedirs(os.path.dirname(path))
    return open(path, 'w')


def _create_html_file(path: str) -> object:
    return _create_file(os.path.join(path, 'index.html'))


def _render_public(site: Site, environment: Environment) -> None:
    site.resources.copytree('public', site.configuration.output_directory_path)
    render_tree(site.configuration.output_directory_path, environment)


def render_tree(path: str, environment: Environment) -> None:
    template_loader = FileSystemLoader('/')
    for file_source_path in iterfiles(path):
        if file_source_path.endswith('.j2'):
            file_destination_path = file_source_path[:-3]
            template = template_loader.load(environment, file_source_path, environment.globals)
            with open(file_destination_path, 'w') as f:
                f.write(template.render())
            os.remove(file_source_path)


def _render_documents(site: Site) -> None:
    documents_directory_path = os.path.join(
        site.configuration.output_directory_path, 'document')
    makedirs(documents_directory_path)
    for document in site.ancestry.documents.values():
        destination = os.path.join(documents_directory_path,
                                   document.id + splitext(document.file.path)[1])
        shutil.copy2(document.file.path, destination)


def _render_entity_type(site: Site, environment: Environment, entities: Iterable[Entity],
                        entity_type_name: str) -> None:
    entity_type_path = os.path.join(
        site.configuration.output_directory_path, entity_type_name)
    with _create_html_file(entity_type_path) as f:
        f.write(environment.get_template('page/list-%s.html.j2' % entity_type_name).render({
            'entity_type_name': entity_type_name,
            'entities': entities,
        }))
    for entity in entities:
        _render_entity(site, environment, entity, entity_type_name)


def _render_entity(site: Site, environment: Environment, entity: Entity, entity_type_name: str) -> None:
    entity_path = os.path.join(
        site.configuration.output_directory_path, entity_type_name, entity.id)
    with _create_html_file(entity_path) as f:
        f.write(environment.get_template('page/%s.html.j2' % entity_type_name).render({
            entity_type_name: entity,
        }))


def _render_flatten(items):
    for item in items:
        for child in item:
            yield child


def _render_walk(item, attribute_name):
    return walk(item, attribute_name)


def _render_json(data: Any) -> Union[str, Markup]:
    return dumps(data, cls=JSONEncoder)


_paragraph_re = re.compile(r'(?:\r\n|\r|\n){2,}')


@evalcontextfilter
def _render_html_paragraphs(eval_ctx, text: str) -> Union[str, Markup]:
    """Converts newlines to <p> and <br> tags.

    Taken from http://jinja.pocoo.org/docs/2.10/api/#custom-filters."""
    result = u'\n\n'.join(u'<p>%s</p>' % p.replace('\n', Markup('<br>\n'))
                          for p in _paragraph_re.split(escape(text)))
    if eval_ctx.autoescape:
        result = Markup(result)
    return result


def _render_format_degrees(degrees):
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
def _render_map(*args, **kwargs):
    if len(args) == 3 and isinstance(args[2], Macro):
        seq = args[1]
        func = args[2]
    else:
        seq, func = prepare_map(args, kwargs)
    if seq:
        for item in seq:
            yield func(item)


@contextfilter
def _render_takewhile(context, seq, *args, **kwargs):
    try:
        name = args[0]
        args = args[1:]

        def func(item):
            return context.environment.call_test(name, item, args, kwargs)
    except LookupError:
        func = bool
    if seq:
        yield from takewhile(func, seq)


def _render_url(configuration: Configuration, path: str, absolute=False):
    url = _render_file_url(configuration, path, absolute)
    if not configuration.clean_urls:
        url += '/index.html'
    return url


def _render_file_url(configuration: Configuration, path: str, absolute=False):
    url = configuration.base_url if absolute else ''
    path = (configuration.root_path.strip('/') + '/' + path.strip('/')).strip('/')
    url += '/' + path
    return url


class Plugins:
    def __init__(self, plugins: Dict[Type, Plugin]):
        self._plugins = plugins

    def __getitem__(self, plugin_type_name):
        return self._plugins[self._type(plugin_type_name)]

    def __contains__(self, plugin_type_name):
        return self._type(plugin_type_name) in self._plugins

    def _type(self, plugin_type_name: str):
        plugin_module_name, plugin_class_name = plugin_type_name.rsplit('.', 1)
        return getattr(import_module(plugin_module_name), plugin_class_name)
