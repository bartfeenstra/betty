import asyncio
import json
import logging
import math
import os
import shutil
from contextlib import suppress
from pathlib import Path
from typing import Iterable, Any, TYPE_CHECKING, cast, AsyncContextManager, List

import aiofiles
from aiofiles import os as aiofiles_os
from aiofiles.threadpool.text import AsyncTextIOWrapper
from babel import Locale
from jinja2 import TemplateNotFound

from betty.app import App
from betty.jinja2 import Environment
from betty.json import JSONEncoder
from betty.locale import bcp_47_to_rfc_1766
from betty.model import EntityCollection, Entity
from betty.model.ancestry import File, Person, Place, Event, Citation, Source, Note
from betty.openapi import build_specification

if TYPE_CHECKING:
    from betty.builtins import _


try:
    from resource import getrlimit, RLIMIT_NOFILE  # type: ignore
    _GENERATE_CONCURRENCY = math.ceil(getrlimit(RLIMIT_NOFILE)[0] / 2)
except ImportError:
    _GENERATE_CONCURRENCY = 999


def getLogger() -> logging.Logger:
    return logging.getLogger(__name__)


class Generator:
    async def generate(self) -> None:
        raise NotImplementedError


async def generate(app: App) -> None:
    shutil.rmtree(app.project.configuration.output_directory_path, ignore_errors=True)
    await aiofiles_os.makedirs(app.project.configuration.output_directory_path)
    await asyncio.gather(
        _generate(app),
        app.dispatcher.dispatch(Generator)(),
    )
    os.chmod(app.project.configuration.output_directory_path, 0o755)
    for directory_path_str, subdirectory_names, file_names in os.walk(app.project.configuration.output_directory_path):
        directory_path = Path(directory_path_str)
        for subdirectory_name in subdirectory_names:
            os.chmod(directory_path / subdirectory_name, 0o755)
        for file_name in file_names:
            os.chmod(directory_path / file_name, 0o644)
    app.wait()


async def _generate(app: App) -> None:
    logger = getLogger()
    await app.assets.copytree(Path('public') / 'static', app.project.configuration.www_directory_path)
    await app.renderer.render_tree(app.project.configuration.www_directory_path)
    for locale_configuration in app.project.configuration.locales:
        locale = locale_configuration.locale
        with app.acquire_locale(locale):
            if app.project.configuration.multilingual:
                www_directory_path = app.project.configuration.www_directory_path / locale_configuration.alias
            else:
                www_directory_path = app.project.configuration.www_directory_path

            await app.assets.copytree(Path('public') / 'localized', www_directory_path)
            await app.renderer.render_tree(www_directory_path)

            coroutines = [
                *[
                    coroutine
                    for entities, entity_type_name in [
                        (app.project.ancestry.entities[File], 'file'),
                        (app.project.ancestry.entities[Person], 'person'),
                        (app.project.ancestry.entities[Place], 'place'),
                        (app.project.ancestry.entities[Event], 'event'),
                        (app.project.ancestry.entities[Citation], 'citation'),
                        (app.project.ancestry.entities[Source], 'source'),
                    ]
                    async for coroutine in _generate_entity_type(
                        www_directory_path,
                        cast(EntityCollection[Entity], entities),
                        entity_type_name,
                        app,
                        locale,
                        app.jinja2_environment,
                    )
                ],
                _generate_entity_type_list_json(www_directory_path, app.project.ancestry.entities[Note], 'note', app),
                *[
                    _generate_entity_json(www_directory_path, note, 'note', app)
                    for note in app.project.ancestry.entities[Note]
                ],
                _generate_openapi(www_directory_path, app)
            ]
            # Batch all coroutines to reduce the risk of "too many open files" errors.
            for i in range(0, len(coroutines), _GENERATE_CONCURRENCY):
                await asyncio.gather(*coroutines[i:i + _GENERATE_CONCURRENCY])
            locale_label = Locale.parse(bcp_47_to_rfc_1766(locale)).get_display_name(locale=bcp_47_to_rfc_1766(app.locale))
            logger.info(_('Generated pages for {file_count} files in {locale}.').format(file_count=len(app.project.ancestry.entities[File]), locale=locale_label))
            logger.info(_('Generated pages for {person_count} people in {locale}.').format(person_count=len(app.project.ancestry.entities[Person]), locale=locale_label))
            logger.info(_('Generated pages for {place_count} places in {locale}.').format(place_count=len(app.project.ancestry.entities[Place]), locale=locale_label))
            logger.info(_('Generated pages for {event_count} events in {locale}.').format(event_count=len(app.project.ancestry.entities[Event]), locale=locale_label))
            logger.info(_('Generated pages for {citation_count} citations in {locale}.').format(citation_count=len(app.project.ancestry.entities[Citation]), locale=locale_label))
            logger.info(_('Generated pages for {source_count} sources in {locale}.').format(source_count=len(app.project.ancestry.entities[Source]), locale=locale_label))
            logger.info(_('Generated pages for {note_count} notes in {locale}.').format(note_count=len(app.project.ancestry.entities[Note]), locale=locale_label))
            logger.info(_('Generated OpenAPI documentation in {locale}.').format(locale=locale_label))


def _create_file(path: Path) -> AsyncContextManager[AsyncTextIOWrapper]:
    path.parent.mkdir(exist_ok=True, parents=True)
    return cast(AsyncContextManager[AsyncTextIOWrapper], aiofiles.open(path, 'w', encoding='utf-8'))


def _create_html_resource(path: Path) -> AsyncContextManager[AsyncTextIOWrapper]:
    return _create_file(path / 'index.html')


def _create_json_resource(path: Path) -> AsyncContextManager[AsyncTextIOWrapper]:
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
            environment,
        ):
            yield coroutine


async def _generate_entity_type_list_html(www_directory_path: Path, entities: Iterable[Any], entity_type_name: str,
                                          environment: Environment) -> None:
    entity_type_path = www_directory_path / entity_type_name
    with suppress(TemplateNotFound):
        template = environment.negotiate_template([
            f'entity/page-list--{entity_type_name}.html.j2',
            'entity/page-list.html.j2',
        ])
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
        cast(List[str], data['collection']).append(
            app.url_generator.generate(
                entity,
                'application/json',
                absolute=True,
            ))
    rendered_json = json.dumps(data)
    async with _create_json_resource(entity_type_path) as f:
        await f.write(rendered_json)


async def _generate_entity(www_directory_path: Path, entity: Any, entity_type_name: str, app: App, environment: Environment):
    yield _generate_entity_html(www_directory_path, entity, entity_type_name, environment)
    yield _generate_entity_json(www_directory_path, entity, entity_type_name, app)


async def _generate_entity_html(www_directory_path: Path, entity: Any, entity_type_name: str, environment: Environment) -> None:
    entity_path = www_directory_path / entity_type_name / entity.id
    rendered_html = environment.negotiate_template([
        f'entity/page--{entity_type_name}.html.j2',
        'entity/page.html.j2',
    ]).render({
        'page_resource': entity,
        'entity_type_name': entity_type_name,
        'entity': entity,
    })
    async with _create_html_resource(entity_path) as f:
        await f.write(rendered_html)


async def _generate_entity_json(www_directory_path: Path, entity: Any, entity_type_name: str, app: App) -> None:
    entity_path = www_directory_path / entity_type_name / entity.id
    rendered_json = json.dumps(entity, cls=JSONEncoder.get_factory(app))
    async with _create_json_resource(entity_path) as f:
        await f.write(rendered_json)


async def _generate_openapi(www_directory_path: Path, app: App) -> None:
    api_directory_path = www_directory_path / 'api'
    api_directory_path.mkdir(exist_ok=True, parents=True)
    rendered_json = json.dumps(build_specification(app))
    async with _create_json_resource(api_directory_path) as f:
        await f.write(rendered_json)
