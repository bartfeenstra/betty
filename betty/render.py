import calendar
import os
import re
import shutil
from itertools import takewhile
from json import dumps
from os.path import join, splitext
from typing import Iterable, Union, Any

from geopy import units
from geopy.format import DEGREES_FORMAT
from jinja2 import Environment, select_autoescape, evalcontextfilter, escape, FileSystemLoader, contextfilter
from jinja2.filters import prepare_map
from jinja2.runtime import Macro
from markupsafe import Markup

import betty
from betty.ancestry import Entity
from betty.event import POST_RENDER_EVENT
from betty.json import JSONEncoder
from betty.path import iterfiles
from betty.site import Site


def render(site: Site) -> None:
    environment = Environment(
        loader=FileSystemLoader(join(betty.RESOURCE_PATH, 'templates')),
        autoescape=select_autoescape(['html'])
    )
    environment.globals['site'] = site
    environment.globals['calendar'] = calendar
    environment.filters['map'] = _render_map
    environment.filters['flatten'] = _render_flatten
    environment.filters['walk'] = _render_walk
    environment.filters['takewhile'] = _render_takewhile
    environment.filters['json'] = _render_json
    environment.filters['paragraphs'] = _render_html_paragraphs
    environment.filters['format_degrees'] = _render_format_degrees

    _render_public(site, environment)
    _render_webpack(site, environment)
    _render_documents(site)
    _render_entity_type(site, environment,
                        site.ancestry.people.values(), 'person')
    _render_entity_type(site, environment,
                        site.ancestry.places.values(), 'place')
    _render_entity_type(site, environment,
                        site.ancestry.events.values(), 'event')
    site.event_dispatcher.dispatch(POST_RENDER_EVENT, site, environment)


def _create_directory(path: str) -> None:
    os.makedirs(path, 0o755, True)


def _create_file(path: str) -> object:
    _create_directory(os.path.dirname(path))
    return open(path, 'w')


def _create_html_file(path: str) -> object:
    return _create_file(os.path.join(path, 'index.html'))


def _copytree(environment: Environment, source_path: str, destination_path: str) -> None:
    template_loader = FileSystemLoader('/')
    for file_source_path in iterfiles(source_path):
        file_destination_path = join(
            destination_path, file_source_path[len(source_path) + 1:])
        if file_source_path.endswith('.j2'):
            file_destination_path = file_destination_path[:-3]
            with _create_file(file_destination_path) as f:
                template = template_loader.load(
                    environment, file_source_path, environment.globals)
                f.write(template.render())
        else:
            _create_directory(os.path.dirname(file_destination_path))
            shutil.copy2(file_source_path, file_destination_path)


def _render_public(site, environment) -> None:
    _copytree(environment, join(betty.RESOURCE_PATH, 'public'),
              site.configuration.output_directory_path)


def _render_documents(site: Site) -> None:
    documents_directory_path = os.path.join(
        site.configuration.output_directory_path, 'document')
    _create_directory(documents_directory_path)
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
    children = getattr(item, attribute_name)

    # If the child has the requested attribute, yield it,
    if hasattr(children, attribute_name):
        yield children
        yield from _render_walk(children, attribute_name)

    # Otherwise loop over the children and yield their attributes.
    try:
        children = iter(children)
    except TypeError:
        return
    for child in children:
        yield child
        yield from _render_walk(child, attribute_name)


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
