import asyncio
import logging
import os
from json import dump
from os import chmod
from os.path import join
from typing import Iterable, Any, List

from jinja2 import Environment, TemplateNotFound

from betty import sass
from betty.config import Configuration
from betty.event import Event
from betty.fs import makedirs
from betty.jinja2 import create_environment, render_tree
from betty.json import JSONEncoder
from betty.locale import Translations
from betty.openapi import build_specification
from betty.site import Site
from betty.url import SiteUrlGenerator, StaticPathUrlGenerator


class PostRenderEvent(Event):
    def __init__(self, environment: Environment):
        self._environment = environment

    @property
    def environment(self) -> Environment:
        return self._environment


def render(site: Site) -> None:
    site.resources.copytree(join('public', 'static'),
                            site.configuration.www_directory_path)
    static_environment = create_environment(site)
    render_tree(site.configuration.www_directory_path,
                static_environment, site.configuration)
    sass.render_tree(site.configuration.www_directory_path)
    loop = asyncio.new_event_loop()
    loop.run_until_complete(_render_localized(site))
    loop.close()
    chmod(site.configuration.www_directory_path, 0o755)
    for directory_path, subdirectory_names, file_names in os.walk(site.configuration.www_directory_path):
        for subdirectory_name in subdirectory_names:
            chmod(join(directory_path, subdirectory_name), 0o755)
        for file_name in file_names:
            chmod(join(directory_path, file_name), 0o644)
    site.event_dispatcher.dispatch(PostRenderEvent(static_environment))


async def _render_localized(site: Site):
    logger = logging.getLogger()
    for locale, locale_configuration in site.configuration.locales.items():
        localized_environment = create_environment(site, locale)
        if site.configuration.multilingual:
            www_directory_path = join(
                site.configuration.www_directory_path, locale_configuration.alias)
        else:
            www_directory_path = site.configuration.www_directory_path

        site.resources.copytree(
            join('public', 'localized'), www_directory_path)
        render_tree(www_directory_path,
                    localized_environment, site.configuration)

        await _render_entities(site, www_directory_path, locale, localized_environment)

        with Translations(site.translations[locale]):
            _render_openapi(www_directory_path, site)
        logger.info('Rendered OpenAPI documentation.')


async def _render_entities(site: Site, www_directory_path: str, locale: str, environment: Environment) -> None:
    await _render_entity_type(www_directory_path, list(site.ancestry.files.values()
                                                       ), 'file', site.configuration, locale, environment)
    await _render_entity_type(www_directory_path, list(site.ancestry.people.values()
                                                       ), 'person', site.configuration, locale, environment)
    await _render_entity_type(www_directory_path, list(site.ancestry.places.values()
                                                       ), 'place', site.configuration, locale, environment)
    await _render_entity_type(www_directory_path, list(site.ancestry.events.values()
                                                       ), 'event', site.configuration, locale, environment)
    await _render_entity_type(www_directory_path, list(site.ancestry.citations.values()
                                                       ), 'citation', site.configuration, locale, environment)
    await _render_entity_type(www_directory_path, list(site.ancestry.sources.values()
                                                       ), 'source', site.configuration, locale, environment)


def _create_file(path: str) -> object:
    makedirs(os.path.dirname(path))
    return open(path, 'w')


def _create_html_resource(path: str) -> object:
    return _create_file(os.path.join(path, 'index.html'))


def _create_json_resource(path: str) -> object:
    return _create_file(os.path.join(path, 'index.json'))


async def _render_entity_type(www_directory_path: str, entities: List[Any], entity_type_name: str,
                              configuration: Configuration, locale: str, environment: Environment) -> None:
    _render_entity_type_list_html(
        www_directory_path, entities, entity_type_name, environment)
    _render_entity_type_list_json(
        www_directory_path, entities, entity_type_name, configuration)
    for entity in entities:
        await _render_entity(www_directory_path, entity,
                             entity_type_name, configuration, locale, environment)
    logging.getLogger().info('Rendered %d %s entities in %s.' % (len(entities), entity_type_name, locale))


def _render_entity_type_list_html(www_directory_path: str, entities: Iterable[Any], entity_type_name: str,
                                  environment: Environment) -> None:
    entity_type_path = os.path.join(www_directory_path, entity_type_name)
    try:
        template = environment.get_template(
            'page/list-%s.html.j2' % entity_type_name)
        with _create_html_resource(entity_type_path) as f:
            f.write(template.render({
                'resource': '/%s/index.html' % entity_type_name,
                'entity_type_name': entity_type_name,
                'entities': entities,
            }))
    except TemplateNotFound:
        pass


def _render_entity_type_list_json(www_directory_path: str, entities: Iterable[Any], entity_type_name: str,
                                  configuration: Configuration) -> None:
    entity_type_path = os.path.join(www_directory_path, entity_type_name)
    with _create_json_resource(entity_type_path) as f:
        url_generator = SiteUrlGenerator(configuration)
        data = {
            '$schema': StaticPathUrlGenerator(configuration).generate(
                'schema.json#/definitions/%sCollection' % entity_type_name, absolute=True),
            'collection': []
        }
        for entity in entities:
            data['collection'].append(url_generator.generate(
                entity, 'application/json', absolute=True))
        dump(data, f)


async def _render_entity(www_directory_path: str, entity: Any, entity_type_name: str, configuration: Configuration,
                         locale: str, environment: Environment) -> None:
    await _render_entity_html(www_directory_path, entity,
                              entity_type_name, environment)
    await _render_entity_json(www_directory_path, entity,
                              entity_type_name, configuration, locale)


async def _render_entity_html(www_directory_path: str, entity: Any, entity_type_name: str,
                              environment: Environment) -> None:
    entity_path = os.path.join(www_directory_path, entity_type_name, entity.id)
    with _create_html_resource(entity_path) as f:
        f.write(environment.get_template('page/%s.html.j2' % entity_type_name).render({
            'resource': entity,
            'entity_type_name': entity_type_name,
            entity_type_name: entity,
        }))


async def _render_entity_json(www_directory_path: str, entity: Any, entity_type_name: str, configuration: Configuration,
                              locale: str) -> None:
    entity_path = os.path.join(www_directory_path, entity_type_name, entity.id)
    with _create_json_resource(entity_path) as f:
        dump(entity, f, cls=JSONEncoder.get_factory(configuration, locale))


def _render_openapi(www_directory_path: str, site: Site) -> None:
    with open(join(www_directory_path, 'api', 'index.json'), 'w') as f:
        dump(build_specification(site), f)
