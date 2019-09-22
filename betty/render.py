import logging
import os
from os import chmod
from os.path import join
from typing import Iterable, Any

from jinja2 import Environment, TemplateNotFound

from betty import sass
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
    logger = logging.getLogger()
    site.resources.copytree(join('public', 'static'),
                            site.configuration.www_directory_path)
    render_tree(site.configuration.www_directory_path,
                create_environment(site))
    sass.render_tree(site.configuration.www_directory_path)
    for locale in site.configuration.locales:
        environment = create_environment(site, locale)
        if site.configuration.multilingual:
            www_directory_path = join(
                site.configuration.www_directory_path, locale.get_identifier())
        else:
            www_directory_path = site.configuration.www_directory_path

        site.resources.copytree(
            join('public', 'localized'), www_directory_path)
        render_tree(www_directory_path, environment)

        _render_entity_type(www_directory_path, environment,
                            site.ancestry.files.values(), 'file')
        logger.info('Rendered %d files in %s.' %
                    (len(site.ancestry.files), locale))
        _render_entity_type(www_directory_path, environment,
                            site.ancestry.people.values(), 'person')
        logger.info('Rendered %d people in %s.' %
                    (len(site.ancestry.people), locale))
        _render_entity_type(www_directory_path, environment,
                            site.ancestry.places.values(), 'place')
        logger.info('Rendered %d places in %s.' %
                    (len(site.ancestry.places), locale))
        _render_entity_type(www_directory_path, environment,
                            site.ancestry.events.values(), 'event')
        logger.info('Rendered %d events in %s.' %
                    (len(site.ancestry.events), locale))
        _render_entity_type(www_directory_path, environment,
                            site.ancestry.citations.values(), 'citation')
        logger.info('Rendered %d citations in %s.' %
                    (len(site.ancestry.citations), locale))
        _render_entity_type(www_directory_path, environment,
                            site.ancestry.sources.values(), 'source')
        logger.info('Rendered %d sources in %s.' %
                    (len(site.ancestry.sources), locale))
    chmod(site.configuration.www_directory_path, 0o755)
    for directory_path, subdirectory_names, file_names in os.walk(site.configuration.www_directory_path):
        for subdirectory_name in subdirectory_names:
            chmod(join(directory_path, subdirectory_name), 0o755)
        for file_name in file_names:
            chmod(join(directory_path, file_name), 0o644)
    site.event_dispatcher.dispatch(PostRenderEvent(environment))


def _create_file(path: str) -> object:
    makedirs(os.path.dirname(path))
    return open(path, 'w')


def _create_html_file(path: str) -> object:
    return _create_file(os.path.join(path, 'index.html'))


def _render_entity_type(www_directory_path: str, environment: Environment, entities: Iterable[Any],
                        entity_type_name: str) -> None:
    entity_type_path = os.path.join(www_directory_path, entity_type_name)
    try:
        template = environment.get_template(
            'page/list-%s.html.j2' % entity_type_name)
        with _create_html_file(entity_type_path) as f:
            f.write(template.render({
                'entity_type_name': entity_type_name,
                'entities': entities,
            }))
    except TemplateNotFound:
        pass
    for entity in entities:
        _render_entity(www_directory_path, environment,
                       entity, entity_type_name)


def _render_entity(www_directory_path: str, environment: Environment, entity: Any, entity_type_name: str) -> None:
    entity_path = os.path.join(www_directory_path, entity_type_name, entity.id)
    with _create_html_file(entity_path) as f:
        f.write(environment.get_template('page/%s.html.j2' % entity_type_name).render({
            entity_type_name: entity,
        }))
