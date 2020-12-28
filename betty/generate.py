import asyncio
import logging
import os
from contextlib import suppress
from json import dump
from os import chmod
from os.path import join
from typing import Iterable, Any

from babel import Locale
from jinja2 import Environment, TemplateNotFound

from betty.fs import makedirs
from betty.json import JSONEncoder
from betty.openapi import build_specification
from betty.app import App


class Generator:
    async def generate(self) -> None:
        raise NotImplementedError


async def generate(app: App) -> None:

    await asyncio.gather(*[
        _generate(app),
        app.dispatcher.dispatch(Generator, 'generate')(),
    ])


async def _generate(app: App) -> None:
    logger = logging.getLogger()
    await app.assets.copytree(join('public', 'static'), app.configuration.www_directory_path)
    await app.renderer.render_tree(app.configuration.www_directory_path)
    for locale, locale_configuration in app.configuration.locales.items():
        async with app.with_locale(locale) as app:
            if app.configuration.multilingual:
                www_directory_path = join(
                    app.configuration.www_directory_path, locale_configuration.alias)
            else:
                www_directory_path = app.configuration.www_directory_path

            await app.assets.copytree(join('public', 'localized'), www_directory_path)
            await app.renderer.render_tree(www_directory_path)

            locale_label = Locale.parse(locale, '-').get_display_name()
            await _generate_entity_type(www_directory_path, app.ancestry.files.values(
            ), 'file', app, locale, app.jinja2_environment)
            logger.info('Generated pages for %d files in %s.' %
                        (len(app.ancestry.files), locale_label))
            await _generate_entity_type(www_directory_path, app.ancestry.people.values(
            ), 'person', app, locale, app.jinja2_environment)
            logger.info('Generated pages for %d people in %s.' %
                        (len(app.ancestry.people), locale_label))
            await _generate_entity_type(www_directory_path, app.ancestry.places.values(
            ), 'place', app, locale, app.jinja2_environment)
            logger.info('Generated pages for %d places in %s.' %
                        (len(app.ancestry.places), locale_label))
            await _generate_entity_type(www_directory_path, app.ancestry.events.values(
            ), 'event', app, locale, app.jinja2_environment)
            logger.info('Generated pages for %d events in %s.' %
                        (len(app.ancestry.events), locale_label))
            await _generate_entity_type(www_directory_path, app.ancestry.citations.values(
            ), 'citation', app, locale, app.jinja2_environment)
            logger.info('Generated pages for %d citations in %s.' %
                        (len(app.ancestry.citations), locale_label))
            await _generate_entity_type(www_directory_path, app.ancestry.sources.values(
            ), 'source', app, locale, app.jinja2_environment)
            logger.info('Generated pages for %d sources in %s.' %
                        (len(app.ancestry.sources), locale_label))
            _generate_entity_type_list_json(www_directory_path, app.ancestry.notes.values(), 'note', app)
            for note in app.ancestry.notes.values():
                _generate_entity_json(www_directory_path, note, 'note', app, locale)
            logger.info('Generated pages for %d notes in %s.' % (len(app.ancestry.notes), locale_label))
            _generate_openapi(www_directory_path, app)
            logger.info('Generated OpenAPI documentation in %s.', locale_label)
    chmod(app.configuration.www_directory_path, 0o755)
    for directory_path, subdirectory_names, file_names in os.walk(app.configuration.www_directory_path):
        for subdirectory_name in subdirectory_names:
            chmod(join(directory_path, subdirectory_name), 0o755)
        for file_name in file_names:
            chmod(join(directory_path, file_name), 0o644)


def _create_file(path: str) -> object:
    makedirs(os.path.dirname(path))
    return open(path, 'w')


def _create_html_resource(path: str) -> object:
    return _create_file(os.path.join(path, 'index.html'))


def _create_json_resource(path: str) -> object:
    return _create_file(os.path.join(path, 'index.json'))


async def _generate_entity_type(www_directory_path: str, entities: Iterable[Any], entity_type_name: str, app: App,
                                locale: str, environment: Environment) -> None:
    await _generate_entity_type_list_html(
        www_directory_path, entities, entity_type_name, environment)
    _generate_entity_type_list_json(
        www_directory_path, entities, entity_type_name, app)
    for entity in entities:
        await _generate_entity(www_directory_path, entity,
                               entity_type_name, app, locale, environment)


async def _generate_entity_type_list_html(www_directory_path: str, entities: Iterable[Any], entity_type_name: str,
                                          environment: Environment) -> None:
    entity_type_path = os.path.join(www_directory_path, entity_type_name)
    with suppress(TemplateNotFound):
        template = environment.get_template(
            'page/list-%s.html.j2' % entity_type_name)
        with _create_html_resource(entity_type_path) as f:
            f.write(template.render({
                'page_resource': '/%s/index.html' % entity_type_name,
                'entity_type_name': entity_type_name,
                'entities': entities,
            }))


def _generate_entity_type_list_json(www_directory_path: str, entities: Iterable[Any], entity_type_name: str, app: App) -> None:
    entity_type_path = os.path.join(www_directory_path, entity_type_name)
    with _create_json_resource(entity_type_path) as f:
        data = {
            '$schema': app.static_url_generator.generate('schema.json#/definitions/%sCollection' % entity_type_name, absolute=True),
            'collection': []
        }
        for entity in entities:
            data['collection'].append(app.localized_url_generator.generate(
                entity, 'application/json', absolute=True))
        dump(data, f)


async def _generate_entity(www_directory_path: str, entity: Any, entity_type_name: str, app: App, locale: str, environment: Environment) -> None:
    await _generate_entity_html(www_directory_path, entity,
                                entity_type_name, environment)
    _generate_entity_json(www_directory_path, entity,
                          entity_type_name, app, locale)


async def _generate_entity_html(www_directory_path: str, entity: Any, entity_type_name: str, environment: Environment) -> None:
    entity_path = os.path.join(www_directory_path, entity_type_name, entity.id)
    with _create_html_resource(entity_path) as f:
        f.write(environment.get_template('page/%s.html.j2' % entity_type_name).render({
            'page_resource': entity,
            'entity_type_name': entity_type_name,
            entity_type_name: entity,
        }))


def _generate_entity_json(www_directory_path: str, entity: Any, entity_type_name: str, app: App, locale: str) -> None:
    entity_path = os.path.join(www_directory_path, entity_type_name, entity.id)
    with _create_json_resource(entity_path) as f:
        dump(entity, f, cls=JSONEncoder.get_factory(app, locale))


def _generate_openapi(www_directory_path: str, app: App) -> None:
    api_directory_path = join(www_directory_path, 'api')
    makedirs(api_directory_path)
    with open(join(api_directory_path, 'index.json'), 'w') as f:
        dump(build_specification(app), f)
