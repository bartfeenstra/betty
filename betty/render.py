import logging
import os
from contextlib import suppress
from json import dump
from os import chmod
from os.path import join
from typing import Iterable, Any

from jinja2 import Environment, TemplateNotFound

from betty import sass
from betty.event import Event
from betty.fs import makedirs
from betty.jinja2 import create_environment, render_tree
from betty.json import JSONEncoder
from betty.openapi import build_specification
from betty.site import Site


class PostRenderEvent(Event): pass


async def render(site: Site) -> None:
    logger = logging.getLogger()
    site.resources.copytree(join('public', 'static'),
                            site.configuration.www_directory_path)
    environment = create_environment(site)
    await render_tree(site.configuration.www_directory_path, environment, site.configuration)
    await sass.render_tree(site.configuration.www_directory_path)
    for locale, locale_configuration in site.configuration.locales.items():
        async with site.with_locale(locale) as site:
            environment = create_environment(site)
            if site.configuration.multilingual:
                www_directory_path = join(
                    site.configuration.www_directory_path, locale_configuration.alias)
            else:
                www_directory_path = site.configuration.www_directory_path

            site.resources.copytree(
                join('public', 'localized'), www_directory_path)
            await render_tree(www_directory_path, environment, site.configuration)

            await _render_entity_type(www_directory_path, site.ancestry.files.values(
            ), 'file', site, locale, environment)
            logger.info('Rendered %d files in %s.' %
                        (len(site.ancestry.files), locale))
            await _render_entity_type(www_directory_path, site.ancestry.people.values(
            ), 'person', site, locale, environment)
            logger.info('Rendered %d people in %s.' %
                        (len(site.ancestry.people), locale))
            await _render_entity_type(www_directory_path, site.ancestry.places.values(
            ), 'place', site, locale, environment)
            logger.info('Rendered %d places in %s.' %
                        (len(site.ancestry.places), locale))
            await _render_entity_type(www_directory_path, site.ancestry.events.values(
            ), 'event', site, locale, environment)
            logger.info('Rendered %d events in %s.' %
                        (len(site.ancestry.events), locale))
            await _render_entity_type(www_directory_path, site.ancestry.citations.values(
            ), 'citation', site, locale, environment)
            logger.info('Rendered %d citations in %s.' %
                        (len(site.ancestry.citations), locale))
            await _render_entity_type(www_directory_path, site.ancestry.sources.values(
            ), 'source', site, locale, environment)
            logger.info('Rendered %d sources in %s.' %
                        (len(site.ancestry.sources), locale))
            _render_openapi(www_directory_path, site)
            logger.info('Rendered OpenAPI documentation.')
    chmod(site.configuration.www_directory_path, 0o755)
    for directory_path, subdirectory_names, file_names in os.walk(site.configuration.www_directory_path):
        for subdirectory_name in subdirectory_names:
            chmod(join(directory_path, subdirectory_name), 0o755)
        for file_name in file_names:
            chmod(join(directory_path, file_name), 0o644)
    await site.event_dispatcher.dispatch(PostRenderEvent())


def _create_file(path: str) -> object:
    makedirs(os.path.dirname(path))
    return open(path, 'w')


def _create_html_resource(path: str) -> object:
    return _create_file(os.path.join(path, 'index.html'))


def _create_json_resource(path: str) -> object:
    return _create_file(os.path.join(path, 'index.json'))


async def _render_entity_type(www_directory_path: str, entities: Iterable[Any], entity_type_name: str, site: Site,
                              locale: str, environment: Environment) -> None:
    await _render_entity_type_list_html(
        www_directory_path, entities, entity_type_name, environment)
    _render_entity_type_list_json(
        www_directory_path, entities, entity_type_name, site)
    for entity in entities:
        await _render_entity(www_directory_path, entity,
                             entity_type_name, site, locale, environment)


async def _render_entity_type_list_html(www_directory_path: str, entities: Iterable[Any], entity_type_name: str,
                                        environment: Environment) -> None:
    entity_type_path = os.path.join(www_directory_path, entity_type_name)
    with suppress(TemplateNotFound):
        template = environment.get_template(
            'page/list-%s.html.j2' % entity_type_name)
        with _create_html_resource(entity_type_path) as f:
            f.write(await template.render_async({
                'page_resource': '/%s/index.html' % entity_type_name,
                'entity_type_name': entity_type_name,
                'entities': entities,
            }))


def _render_entity_type_list_json(www_directory_path: str, entities: Iterable[Any], entity_type_name: str, site: Site) -> None:
    entity_type_path = os.path.join(www_directory_path, entity_type_name)
    with _create_json_resource(entity_type_path) as f:
        data = {
            '$schema': site.static_url_generator.generate('schema.json#/definitions/%sCollection' % entity_type_name, absolute=True),
            'collection': []
        }
        for entity in entities:
            data['collection'].append(site.localized_url_generator.generate(
                entity, 'application/json', absolute=True))
        dump(data, f)


async def _render_entity(www_directory_path: str, entity: Any, entity_type_name: str, site: Site, locale: str, environment: Environment) -> None:
    await _render_entity_html(www_directory_path, entity,
                              entity_type_name, environment)
    _render_entity_json(www_directory_path, entity,
                        entity_type_name, site, locale)


async def _render_entity_html(www_directory_path: str, entity: Any, entity_type_name: str, environment: Environment) -> None:
    entity_path = os.path.join(www_directory_path, entity_type_name, entity.id)
    with _create_html_resource(entity_path) as f:
        f.write(await environment.get_template('page/%s.html.j2' % entity_type_name).render_async({
            'page_resource': entity,
            'entity_type_name': entity_type_name,
            entity_type_name: entity,
        }))


def _render_entity_json(www_directory_path: str, entity: Any, entity_type_name: str, site: Site, locale: str) -> None:
    entity_path = os.path.join(www_directory_path, entity_type_name, entity.id)
    with _create_json_resource(entity_path) as f:
        dump(entity, f, cls=JSONEncoder.get_factory(site, locale))


def _render_openapi(www_directory_path: str, site: Site) -> None:
    with open(join(www_directory_path, 'api', 'index.json'), 'w') as f:
        dump(build_specification(site), f)
