import asyncio
import json
import logging
import math
import os
from contextlib import suppress
from pathlib import Path
from typing import Iterable, Any

import aiofiles
from babel import Locale
from jinja2 import Environment, TemplateNotFound

from betty.json import JSONEncoder
from betty.model.ancestry import File, Person, Place, Event, Citation, Source, Note
from betty.openapi import build_specification
from betty.app import App

try:
    from resource import getrlimit, RLIMIT_NOFILE
    _GENERATE_CONCURRENCY = math.ceil(getrlimit(RLIMIT_NOFILE)[0] / 2)
except ImportError:
    _GENERATE_CONCURRENCY = 999


def getLogger() -> logging.Logger:
    return logging.getLogger(__name__)


class Generator:
    async def generate(self) -> None:
        raise NotImplementedError


async def generate(app: App) -> None:
    await asyncio.gather(
        _generate(app),
        app.dispatcher.dispatch(Generator, 'generate')(),
    )
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

            coroutines = [
                *[
                    coroutine
                    for entities, entity_type_name in [
                        (app.ancestry.entities[File], 'file'),
                        (app.ancestry.entities[Person], 'person'),
                        (app.ancestry.entities[Place], 'place'),
                        (app.ancestry.entities[Event], 'event'),
                        (app.ancestry.entities[Citation], 'citation'),
                        (app.ancestry.entities[Source], 'source'),
                    ]
                    async for coroutine in _generate_entity_type(www_directory_path, entities, entity_type_name, app, locale, app.jinja2_environment)
                ],
                _generate_entity_type_list_json(www_directory_path, app.ancestry.entities[Note], 'note', app),
                *[
                    _generate_entity_json(www_directory_path, note, 'note', app, locale)
                    for note in app.ancestry.entities[Note]
                ],
                _generate_openapi(www_directory_path, app)
            ]
            # Batch all coroutines to reduce the risk of "too many open files" errors.
            for i in range(0, len(coroutines), _GENERATE_CONCURRENCY):
                await asyncio.gather(*coroutines[i:i + _GENERATE_CONCURRENCY])
            locale_label = Locale.parse(locale, '-').get_display_name()
            logger.info(f'Generated pages for {len(app.ancestry.entities[File])} files in {locale_label}.')
            logger.info(f'Generated pages for {len(app.ancestry.entities[Person])} people in {locale_label}.')
            logger.info(f'Generated pages for {len(app.ancestry.entities[Place])} places in {locale_label}.')
            logger.info(f'Generated pages for {len(app.ancestry.entities[Event])} events in {locale_label}.')
            logger.info(f'Generated pages for {len(app.ancestry.entities[Citation])} citations in {locale_label}.')
            logger.info(f'Generated pages for {len(app.ancestry.entities[Source])} sources in {locale_label}.')
            logger.info(f'Generated pages for {len(app.ancestry.entities[Note])} notes in {locale_label}.')
            logger.info(f'Generated OpenAPI documentation in {locale_label}.')


def _create_file(path: Path) -> object:
    path.parent.mkdir(exist_ok=True, parents=True)
    return aiofiles.open(path, 'w', encoding='utf-8')


def _create_html_resource(path: Path) -> object:
    return _create_file(path / 'index.html')


def _create_json_resource(path: Path) -> object:
    return _create_file(path / 'index.json')


async def _generate_entity_type(www_directory_path: Path, entities: Iterable[Any], entity_type_name: str, app: App,
                                locale: str, environment: Environment):
    yield _generate_entity_type_list_html(
        www_directory_path, entities,
        entity_type_name,
        environment,
    )
    yield _generate_entity_type_list_json(
        www_directory_path,
        entities,
        entity_type_name,
        app,
    )
    for entity in entities:
        async for coroutine in _generate_entity(
            www_directory_path,
            entity,
            entity_type_name,
            app,
            locale,
            environment,
        ):
            yield coroutine


async def _generate_entity_type_list_html(www_directory_path: Path, entities: Iterable[Any], entity_type_name: str,
                                          environment: Environment) -> None:
    entity_type_path = www_directory_path / entity_type_name
    with suppress(TemplateNotFound):
        template = environment.get_template(
            'page/list-%s.html.j2' % entity_type_name)
        rendered_html = template.render({
            'page_resource': '/%s/index.html' % entity_type_name,
            'entity_type_name': entity_type_name,
            'entities': entities,
        })
        async with _create_html_resource(entity_type_path) as f:
            await f.write(rendered_html)


async def _generate_entity_type_list_json(www_directory_path: Path, entities: Iterable[Any], entity_type_name: str, app: App) -> None:
    entity_type_path = www_directory_path / entity_type_name
    data = {
        '$schema': app.static_url_generator.generate('schema.json#/definitions/%sCollection' % entity_type_name, absolute=True),
        'collection': []
    }
    for entity in entities:
        data['collection'].append(app.localized_url_generator.generate(
            entity, 'application/json', absolute=True))
    rendered_json = json.dumps(data)
    async with _create_json_resource(entity_type_path) as f:
        await f.write(rendered_json)


async def _generate_entity(www_directory_path: Path, entity: Any, entity_type_name: str, app: App, locale: str, environment: Environment):
    yield _generate_entity_html(www_directory_path, entity, entity_type_name, environment)
    yield _generate_entity_json(www_directory_path, entity, entity_type_name, app, locale)


async def _generate_entity_html(www_directory_path: Path, entity: Any, entity_type_name: str, environment: Environment) -> None:
    entity_path = www_directory_path / entity_type_name / entity.id
    rendered_html = environment.get_template('page/%s.html.j2' % entity_type_name).render({
        'page_resource': entity,
        'entity_type_name': entity_type_name,
        entity_type_name: entity,
    })
    async with _create_html_resource(entity_path) as f:
        await f.write(rendered_html)


async def _generate_entity_json(www_directory_path: Path, entity: Any, entity_type_name: str, app: App, locale: str) -> None:
    entity_path = www_directory_path / entity_type_name / entity.id
    rendered_json = json.dumps(entity, cls=JSONEncoder.get_factory(app, locale))
    async with _create_json_resource(entity_path) as f:
        await f.write(rendered_json)


async def _generate_openapi(www_directory_path: Path, app: App) -> None:
    api_directory_path = www_directory_path / 'api'
    api_directory_path.mkdir(exist_ok=True, parents=True)
    rendered_json = json.dumps(build_specification(app))
    async with _create_json_resource(api_directory_path) as f:
        await f.write(rendered_json)
