import os
from typing import Iterable, Dict

from jinja2 import Template, Environment, PackageLoader, select_autoescape

from betty.ancestry import Ancestry, Entity


def render(ancestry: Ancestry, output_directory_path: str) -> None:
    _create_directory(output_directory_path)
    render_entity_type(ancestry.people.values(), 'person', output_directory_path)
    render_entity_type(ancestry.families.values(), 'family', output_directory_path)
    render_entity_type(ancestry.places.values(), 'place', output_directory_path)
    render_entity_type(ancestry.events.values(), 'event', output_directory_path)


def _create_directory(path: str) -> None:
    os.makedirs(path, 0o755, True)


def _create_file(path: str) -> object:
    _create_directory(path)
    return open(os.path.join(path, 'index.html'), 'w')


def render_entity_type(entities: Iterable[Entity], entity_type_name: str, output_directory_path: str) -> None:
    entity_type_path = os.path.join(output_directory_path, entity_type_name)
    _render_template(entity_type_path, 'list.html', {
        'entity_type_name': entity_type_name,
        'entities': entities,
    })
    for entity in entities:
        _render_entity(entity, entity_type_name, output_directory_path)


def _render_entity(entity: Entity, entity_type_name: str, output_directory_path: str) -> None:
    entity_path = os.path.join(output_directory_path, entity_type_name, entity.id)
    _render_template(entity_path, '%s.html' % entity_type_name, {
        entity_type_name: entity,
    })


def _render_template(path: str, name: str, data: Dict) -> None:
    with _create_file(path) as f:
        f.write(_get_template(name).render(data))


def _get_template(name: str) -> Template:
    environment = Environment(
        loader=PackageLoader('betty', 'templates'),
        autoescape=select_autoescape(['html'])
    )
    return environment.get_template(name)
