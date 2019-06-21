import os
from typing import Iterable, Any

from jinja2 import Environment

from betty.event import Event
from betty.fs import makedirs
from betty.jinja2 import create_environment, render_tree
from betty.site import Site


class PostRenderEvent(Event):
    def __init__(self, environment: Environment):
        self._environment = environment

    @property
    def environment(self) -> Environment:
        return self._environment


def render(site: Site) -> None:
    environment = create_environment(site)
    _render_public(site, environment)
    _render_entity_type(site, environment,
                        site.ancestry.files.values(), 'file')
    _render_entity_type(site, environment,
                        site.ancestry.people.values(), 'person')
    _render_entity_type(site, environment,
                        site.ancestry.places.values(), 'place')
    _render_entity_type(site, environment,
                        site.ancestry.events.values(), 'event')
    _render_entity_type(site, environment,
                        site.ancestry.references.values(), 'reference')
    site.event_dispatcher.dispatch(PostRenderEvent(environment))


def _create_file(path: str) -> object:
    makedirs(os.path.dirname(path))
    return open(path, 'w')


def _create_html_file(path: str) -> object:
    return _create_file(os.path.join(path, 'index.html'))


def _render_public(site: Site, environment: Environment) -> None:
    site.resources.copytree('public', site.configuration.output_directory_path)
    render_tree(site.configuration.output_directory_path, environment)


def _render_entity_type(site: Site, environment: Environment, entities: Iterable[Any],
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


def _render_entity(site: Site, environment: Environment, entity: Any, entity_type_name: str) -> None:
    entity_path = os.path.join(
        site.configuration.output_directory_path, entity_type_name, entity.id)
    with _create_html_file(entity_path) as f:
        f.write(environment.get_template('page/%s.html.j2' % entity_type_name).render({
            entity_type_name: entity,
        }))
