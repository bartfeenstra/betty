import os
from glob import glob
from os.path import join
from shutil import copytree
from typing import Iterable, Dict

from jinja2 import Template, Environment, PackageLoader, select_autoescape

import betty
from betty.ancestry import Ancestry, Entity
from betty.betty import Betty


def render(ancestry: Ancestry, betty: Betty) -> None:
    _create_directory(betty.output_directory_path)
    _render_assets(betty.output_directory_path)
    render_entity_type(ancestry.people.values(), 'person',
                       betty.output_directory_path)
    render_entity_type(ancestry.families.values(), 'family', betty.output_directory_path)
    render_entity_type(ancestry.places.values(), 'place', betty.output_directory_path)
    render_entity_type(ancestry.events.values(), 'event',
                       betty.output_directory_path)
    _render_content(betty)


def _create_directory(path: str) -> None:
    os.makedirs(path, 0o755, True)


def _create_file(path: str) -> object:
    _create_directory(path)
    return open(os.path.join(path, 'index.html'), 'w')


def _render_assets(path: str) -> None:
    copytree(join(betty.__path__[0], 'assets'), join(path, 'assets'))


def _render_content(betty: Betty) -> None:
    template_root_path = join(betty.betty_root_path, 'templates')
    content_root_path = join(template_root_path, 'content')
    for content_path in glob(join(content_root_path, '**')):
        template_path = content_path[len(template_root_path) + 1:]
        destination_path = content_path[len(content_root_path) + 1:]
        _render_template(join(betty.output_directory_path,
                              destination_path), template_path)


def render_entity_type(entities: Iterable[Entity], entity_type_name: str, output_directory_path: str) -> None:
    entity_type_path = os.path.join(output_directory_path, entity_type_name)
    _render_template(entity_type_path, 'partials/list-%s.html' % entity_type_name, {
        'entity_type_name': entity_type_name,
        'entities': sorted(entities, key=lambda entity: entity.label),
    })
    for entity in entities:
        _render_entity(entity, entity_type_name, output_directory_path)


def _render_entity(entity: Entity, entity_type_name: str, output_directory_path: str) -> None:
    entity_path = os.path.join(
        output_directory_path, entity_type_name, entity.id)
    _render_template(entity_path, 'partials/%s.html' % entity_type_name, {
        entity_type_name: entity,
    })


def _render_template(path: str, name: str, data: Dict = None) -> None:
    with _create_file(path) as f:
        f.write(_get_template(name).render(data or {}))


def _get_template(name: str) -> Template:
    environment = Environment(
        loader=PackageLoader('betty', 'templates'),
        autoescape=select_autoescape(['html'])
    )
    return environment.get_template(name)
