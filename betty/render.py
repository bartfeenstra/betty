import os
import re
import shutil
from glob import glob
from os.path import join, splitext, abspath
from shutil import copytree
from typing import Iterable

from jinja2 import Environment, PackageLoader, select_autoescape, evalcontextfilter, escape
from markupsafe import Markup

import betty
from betty.ancestry import Entity
from betty.site import Site


def render(site: Site) -> None:
    environment = Environment(
        loader=PackageLoader('betty', 'templates'),
        autoescape=select_autoescape(['html'])
    )
    environment.globals['site'] = site
    environment.filters['paragraphs'] = _render_html_paragraphs

    _create_directory(site.configuration.output_directory_path)
    _render_assets(site.configuration.output_directory_path)
    _render_documents(site)
    _render_entity_type(site, environment, site.ancestry.people.values(), 'person')
    _render_entity_type(site, environment, site.ancestry.places.values(), 'place')
    _render_entity_type(site, environment, site.ancestry.events.values(), 'event')
    _render_content(site, environment)


def _create_directory(path: str) -> None:
    os.makedirs(path, 0o755, True)


def _create_file(path: str) -> object:
    _create_directory(os.path.dirname(path))
    return open(path, 'w')


def _create_document(path: str) -> object:
    return _create_file(os.path.join(path, 'index.html'))


def _render_assets(path: str) -> None:
    copytree(join(betty.__path__[0], 'assets'), join(path, 'assets'))


def _render_content(site: Site, environment: Environment) -> None:
    template_root_path = join(abspath(betty.__path__[0]), 'templates')
    content_root_path = join(template_root_path, 'content')
    for content_path in glob(join(content_root_path, '**')):
        template_path = content_path[len(template_root_path) + 1:]
        destination_path = content_path[len(content_root_path) + 1:]
        with _create_file(join(site.configuration.output_directory_path,
                               destination_path)) as f:
            f.write(environment.get_template(template_path).render())


def _render_documents(site: Site) -> None:
    documents_directory_path = os.path.join(site.configuration.output_directory_path, 'document')
    _create_directory(documents_directory_path)
    for document in site.ancestry.documents.values():
        destination = os.path.join(documents_directory_path,
                                   document.id + splitext(document.file.path)[1])
        shutil.copy2(document.file.path, destination)


def _render_entity_type(site: Site, environment: Environment, entities: Iterable[Entity],
                        entity_type_name: str) -> None:
    entity_type_path = os.path.join(site.configuration.output_directory_path, entity_type_name)
    with _create_document(entity_type_path) as f:
        f.write(environment.get_template('partials/list-%s.html' % entity_type_name).render({
            'entity_type_name': entity_type_name,
            'entities': sorted(entities, key=lambda entity: entity.label),
        }))
    for entity in entities:
        _render_entity(site, environment, entity, entity_type_name)


def _render_entity(site: Site, environment: Environment, entity: Entity, entity_type_name: str) -> None:
    entity_path = os.path.join(
        site.configuration.output_directory_path, entity_type_name, entity.id)
    with _create_document(entity_path) as f:
        f.write(environment.get_template('partials/%s.html' % entity_type_name).render({
            entity_type_name: entity,
        }))


_paragraph_re = re.compile(r'(?:\r\n|\r|\n){2,}')


@evalcontextfilter
def _render_html_paragraphs(eval_ctx, text: str) -> str:
    """Converts newlines to <p> and <br> tags.

    Taken from http://jinja.pocoo.org/docs/2.10/api/#custom-filters."""
    result = u'\n\n'.join(u'<p>%s</p>' % p.replace('\n', Markup('<br>\n'))
                          for p in _paragraph_re.split(escape(text)))
    if eval_ctx.autoescape:
        result = Markup(result)
    return result
