import asyncio
import json
import logging
import os
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, cast, AsyncContextManager, List, Type

import aiofiles
import math
from aiofiles import os as aiofiles_os
from aiofiles.threadpool.text import AsyncTextIOWrapper
from babel import Locale

from betty.app import App
from betty.json import JSONEncoder
from betty.locale import bcp_47_to_rfc_1766
from betty.model import get_entity_type_name, UserFacingEntity, get_entity_type
from betty.openapi import build_specification
from betty.string import camel_case_to_kebab_case

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
    entity_types = [
        entity_type
        for entity_type
        in app.entity_types
        if issubclass(entity_type, UserFacingEntity)
    ]
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
                    for entity_type in entity_types
                    async for coroutine in _generate_entity_type(
                        www_directory_path,
                        entity_type,
                        app,
                    )
                ],
                _generate_openapi(www_directory_path, app)
            ]
            # Batch all coroutines to reduce the risk of "too many open files" errors.
            for i in range(0, len(coroutines), _GENERATE_CONCURRENCY):
                await asyncio.gather(*coroutines[i:i + _GENERATE_CONCURRENCY])

        # Log the generated pages.
        locale_label = Locale.parse(bcp_47_to_rfc_1766(locale)).get_display_name(locale=bcp_47_to_rfc_1766(app.configuration.locale or 'en-US'))
        for entity_type in entity_types:
            logger.info(_('Generated pages for {count} {entity_type} in {locale}.').format(
                count=len(app.project.ancestry.entities[entity_type]),
                entity_type=entity_type.entity_type_label_plural(),
                locale=locale_label,
            ))


def _create_file(path: Path) -> AsyncContextManager[AsyncTextIOWrapper]:
    path.parent.mkdir(exist_ok=True, parents=True)
    return cast(AsyncContextManager[AsyncTextIOWrapper], aiofiles.open(path, 'w', encoding='utf-8'))


def _create_html_resource(path: Path) -> AsyncContextManager[AsyncTextIOWrapper]:
    return _create_file(path / 'index.html')


def _create_json_resource(path: Path) -> AsyncContextManager[AsyncTextIOWrapper]:
    return _create_file(path / 'index.json')


async def _generate_entity_type(www_directory_path: Path, entity_type: Type[UserFacingEntity], app: App):
    if entity_type in app.project.configuration.entity_types and app.project.configuration.entity_types[entity_type].generate_html_list:
        yield _generate_entity_type_list_html(
            www_directory_path,
            entity_type,
            app,
        )
    yield _generate_entity_type_list_json(
        www_directory_path,
        entity_type,
        app,
    )
    for entity in app.project.ancestry.entities[entity_type]:
        async for coroutine in _generate_entity(
            www_directory_path,
            entity,
            app,
        ):
            yield coroutine


async def _generate_entity_type_list_html(www_directory_path: Path, entity_type: Type[UserFacingEntity], app: App) -> None:
    entity_type_name_fs = camel_case_to_kebab_case(get_entity_type_name(entity_type))
    entity_type_path = www_directory_path / entity_type_name_fs
    template = app.jinja2_environment.negotiate_template([
        f'entity/page-list--{entity_type_name_fs}.html.j2',
        'entity/page-list.html.j2',
    ])
    rendered_html = template.render({
        'page_resource': f'/{entity_type_name_fs}/index.html',
        'entity_type': entity_type,
        'entities': app.project.ancestry.entities[entity_type],
    })
    async with _create_html_resource(entity_type_path) as f:
        await f.write(rendered_html)
    locale_label = Locale.parse(bcp_47_to_rfc_1766(app.locale)).get_display_name(locale=bcp_47_to_rfc_1766(app.configuration.locale or 'en-US'))
    getLogger().debug(_('Generated the listing HTML page for {entity_type} entities in {locale}.').format(
        entity_type=entity_type.entity_type_label_plural(),
        locale=locale_label,
    ))


async def _generate_entity_type_list_json(www_directory_path: Path, entity_type: Type[UserFacingEntity], app: App) -> None:
    entity_type_name = get_entity_type_name(entity_type)
    entity_type_name_fs = camel_case_to_kebab_case(get_entity_type_name(entity_type))
    entity_type_path = www_directory_path / entity_type_name_fs
    data = {
        '$schema': app.static_url_generator.generate('schema.json#/definitions/%sCollection' % entity_type_name, absolute=True),
        'collection': []
    }
    for entity in app.project.ancestry.entities[entity_type]:
        cast(List[str], data['collection']).append(
            app.url_generator.generate(
                entity,
                'application/json',
                absolute=True,
            ))
    rendered_json = json.dumps(data)
    async with _create_json_resource(entity_type_path) as f:
        await f.write(rendered_json)


async def _generate_entity(www_directory_path: Path, entity: UserFacingEntity, app: App):
    yield _generate_entity_html(www_directory_path, entity, app)
    yield _generate_entity_json(www_directory_path, entity, app)


async def _generate_entity_html(www_directory_path: Path, entity: UserFacingEntity, app: App) -> None:
    entity_type_name_fs = camel_case_to_kebab_case(get_entity_type_name(entity))
    entity_path = www_directory_path / entity_type_name_fs / entity.id
    rendered_html = app.jinja2_environment.negotiate_template([
        f'entity/page--{entity_type_name_fs}.html.j2',
        'entity/page.html.j2',
    ]).render({
        'page_resource': entity,
        'entity_type': get_entity_type(entity),
        'entity': entity,
    })
    async with _create_html_resource(entity_path) as f:
        await f.write(rendered_html)


async def _generate_entity_json(www_directory_path: Path, entity: UserFacingEntity, app: App) -> None:
    entity_type_name_fs = camel_case_to_kebab_case(get_entity_type_name(entity))
    entity_path = www_directory_path / entity_type_name_fs / entity.id
    rendered_json = json.dumps(entity, cls=JSONEncoder.get_factory(app))
    async with _create_json_resource(entity_path) as f:
        await f.write(rendered_json)


async def _generate_openapi(www_directory_path: Path, app: App) -> None:
    api_directory_path = www_directory_path / 'api'
    api_directory_path.mkdir(exist_ok=True, parents=True)
    rendered_json = json.dumps(build_specification(app))
    async with _create_json_resource(api_directory_path) as f:
        await f.write(rendered_json)
