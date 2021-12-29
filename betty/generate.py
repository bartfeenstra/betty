import asyncio
import logging
import os
from contextlib import suppress
from json import dump
from pathlib import Path
from typing import Iterable, Any

from babel import Locale
from jinja2 import Environment, TemplateNotFound

from betty.json import JSONEncoder
from betty.model.ancestry import File, Person, Place, Event, Citation, Source, Note
from betty.openapi import build_specification
from betty.app import App


def getLogger() -> logging.Logger:
    return logging.getLogger(__name__)


class Generator:
    async def generate(self) -> None:
        raise NotImplementedError


async def generate(app: App) -> None:
    await asyncio.gather(*[
        _generate(app),
        app.dispatcher.dispatch(Generator, 'generate')(),
    ])
    os.chmod(app.configuration.output_directory_path, 0o755)
    for directory_path_str, subdirectory_names, file_names in os.walk(app.configuration.output_directory_path):
        directory_path = Path(directory_path_str)
        for subdirectory_name in subdirectory_names:
            os.chmod(directory_path / subdirectory_name, 0o755)
        for file_name in file_names:
            os.chmod(directory_path / file_name, 0o644)


async def _generate(app: App) -> None:
    logger = getLogger()
    await app.assets.copytree(Path('public') / 'static', app.configuration.www_directory_path)
    await app.renderer.render_tree(app.configuration.www_directory_path)
    for locale_configuration in app.configuration.locales:
        locale = locale_configuration.locale
        async with app.with_locale(locale) as app:
            if app.configuration.multilingual:
                www_directory_path = app.configuration.www_directory_path / locale_configuration.alias
            else:
                www_directory_path = app.configuration.www_directory_path

            await app.assets.copytree(Path('public') / 'localized', www_directory_path)
            await app.renderer.render_tree(www_directory_path)

            locale_label = Locale.parse(locale, '-').get_display_name()
            await _generate_entity_type(www_directory_path, app.ancestry.entities[File], 'file', app, locale, app.jinja2_environment)
            logger.info('Generated pages for %d files in %s.' %
                        (len(app.ancestry.entities[File]), locale_label))
            await _generate_entity_type(www_directory_path, app.ancestry.entities[Person], 'person', app, locale, app.jinja2_environment)
            logger.info('Generated pages for %d people in %s.' %
                        (len(app.ancestry.entities[Person]), locale_label))
            await _generate_entity_type(www_directory_path, app.ancestry.entities[Place], 'place', app, locale, app.jinja2_environment)
            logger.info('Generated pages for %d places in %s.' %
                        (len(app.ancestry.entities[Place]), locale_label))
            await _generate_entity_type(www_directory_path, app.ancestry.entities[Event], 'event', app, locale, app.jinja2_environment)
            logger.info('Generated pages for %d events in %s.' %
                        (len(app.ancestry.entities[Event]), locale_label))
            await _generate_entity_type(www_directory_path, app.ancestry.entities[Citation], 'citation', app, locale, app.jinja2_environment)
            logger.info('Generated pages for %d citations in %s.' %
                        (len(app.ancestry.entities[Citation]), locale_label))
            await _generate_entity_type(www_directory_path, app.ancestry.entities[Source], 'source', app, locale, app.jinja2_environment)
            logger.info('Generated pages for %d sources in %s.' %
                        (len(app.ancestry.entities[Source]), locale_label))
            _generate_entity_type_list_json(www_directory_path, app.ancestry.entities[Note], 'note', app)
            for note in app.ancestry.entities[Note]:
                _generate_entity_json(www_directory_path, note, 'note', app, locale)
            logger.info('Generated pages for %d notes in %s.' % (len(app.ancestry.entities[Note]), locale_label))
            _generate_openapi(www_directory_path, app)
            logger.info('Generated OpenAPI documentation in %s.', locale_label)


def _create_file(path: Path) -> object:
    path.parent.mkdir(exist_ok=True, parents=True)
    return open(path, 'w', encoding='utf-8')


def _create_html_resource(path: Path) -> object:
    return _create_file(path / 'index.html')


def _create_json_resource(path: Path) -> object:
    return _create_file(path / 'index.json')


async def _generate_entity_type(www_directory_path: Path, entities: Iterable[Any], entity_type_name: str, app: App,
                                locale: str, environment: Environment) -> None:
    await _generate_entity_type_list_html(
        www_directory_path, entities, entity_type_name, environment)
    _generate_entity_type_list_json(
        www_directory_path, entities, entity_type_name, app)
    for entity in entities:
        await _generate_entity(www_directory_path, entity,
                               entity_type_name, app, locale, environment)


async def _generate_entity_type_list_html(www_directory_path: Path, entities: Iterable[Any], entity_type_name: str,
                                          environment: Environment) -> None:
    entity_type_path = www_directory_path / entity_type_name
    with suppress(TemplateNotFound):
        template = environment.get_template(
            'page/list-%s.html.j2' % entity_type_name)
        with _create_html_resource(entity_type_path) as f:
            f.write(template.render({
                'page_resource': '/%s/index.html' % entity_type_name,
                'entity_type_name': entity_type_name,
                'entities': entities,
            }))


def _generate_entity_type_list_json(www_directory_path: Path, entities: Iterable[Any], entity_type_name: str, app: App) -> None:
    entity_type_path = www_directory_path / entity_type_name
    with _create_json_resource(entity_type_path) as f:
        data = {
            '$schema': app.static_url_generator.generate('schema.json#/definitions/%sCollection' % entity_type_name, absolute=True),
            'collection': []
        }
        for entity in entities:
            data['collection'].append(app.localized_url_generator.generate(
                entity, 'application/json', absolute=True))
        dump(data, f)


async def _generate_entity(www_directory_path: Path, entity: Any, entity_type_name: str, app: App, locale: str, environment: Environment) -> None:
    await _generate_entity_html(www_directory_path, entity,
                                entity_type_name, environment)
    _generate_entity_json(www_directory_path, entity,
                          entity_type_name, app, locale)


async def _generate_entity_html(www_directory_path: Path, entity: Any, entity_type_name: str, environment: Environment) -> None:
    entity_path = www_directory_path / entity_type_name / entity.id
    with _create_html_resource(entity_path) as f:
        f.write(environment.get_template('page/%s.html.j2' % entity_type_name).render({
            'page_resource': entity,
            'entity_type_name': entity_type_name,
            entity_type_name: entity,
        }))


def _generate_entity_json(www_directory_path: Path, entity: Any, entity_type_name: str, app: App, locale: str) -> None:
    entity_path = www_directory_path / entity_type_name / entity.id
    with _create_json_resource(entity_path) as f:
        dump(entity, f, cls=JSONEncoder.get_factory(app, locale))


def _generate_openapi(www_directory_path: Path, app: App) -> None:
    api_directory_path = www_directory_path / 'api'
    api_directory_path.mkdir(exist_ok=True, parents=True)
    with open(api_directory_path / 'index.json', 'w', encoding='utf-8') as f:
        dump(build_specification(app), f)
