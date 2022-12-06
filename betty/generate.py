from __future__ import annotations

import asyncio
import json
import logging
import multiprocessing
import os
import queue
import shutil
from contextlib import suppress
from pathlib import Path
from typing import cast, AsyncContextManager, List, Type, Dict

import aiofiles
from aiofiles import os as aiofiles_os
from aiofiles.threadpool.text import AsyncTextIOWrapper
import dill as pickle

from betty.app import App
from betty.asyncio import sync
from betty.locale import get_display_name
from betty.model import get_entity_type_name, UserFacingEntity, get_entity_type, GeneratedEntityId
from betty.openapi import Specification
from betty.project import Project
from betty.string import camel_case_to_kebab_case, camel_case_to_snake_case


def getLogger() -> logging.Logger:
    return logging.getLogger(__name__)


class Generator:
    async def generate(self) -> None:
        raise NotImplementedError


async def generate(app: App) -> None:
    with suppress(FileNotFoundError):
        shutil.rmtree(app.project.configuration.output_directory_path)
    await aiofiles_os.makedirs(app.project.configuration.output_directory_path)
    logging.getLogger().info(app.localizer._('Generating your site to {output_directory}.').format(output_directory=app.project.configuration.output_directory_path))
    await _ConcurrentGenerator.generate(app)
    os.chmod(app.project.configuration.output_directory_path, 0o755)
    for directory_path_str, subdirectory_names, file_names in os.walk(app.project.configuration.output_directory_path):
        directory_path = Path(directory_path_str)
        for subdirectory_name in subdirectory_names:
            os.chmod(directory_path / subdirectory_name, 0o755)
        for file_name in file_names:
            os.chmod(directory_path / file_name, 0o644)
    app.wait()


class _ConcurrentGenerator:
    def __init__(
        self,
        generation_queue: queue.Queue,
        pickled_project: bytes,
        async_concurrency: int,
        caller_locale: str,
    ):
        self._generation_queue = generation_queue
        self._pickled_project = pickled_project
        self._project: Project
        self._async_concurrency = async_concurrency
        self._caller_locale = caller_locale

    @classmethod
    async def generate(cls, app: App) -> None:
        # The static public assets may be overridden depending on the number of locales rendered, so ensure they are
        # generated before anything else.
        await _generate_static_public(app, app.locale)
        generation_queue = cls._build_generation_queue(app)
        pickled_project = pickle.dumps(app.project)
        await asyncio.gather(*[
            app.do_in_process(cls(generation_queue, pickled_project, app.async_concurrency, app.locale))
            for _ in range(0, app.concurrency)
        ])

        # Log the generated pages.
        logger = getLogger()
        for locale in app.project.configuration.locales:
            locale_label = get_display_name(locale, app.localizer.locale)
            for entity_type in app.entity_types:
                if issubclass(entity_type, UserFacingEntity):
                    logger.info(app.localizer._('Generated pages for {count} {entity_type} in {locale}.').format(
                        count=len(app.project.ancestry.entities[entity_type]),
                        entity_type=entity_type.entity_type_label_plural(app.localizer),
                        locale=locale_label,
                    ))

    @classmethod
    def _build_generation_queue(cls, app: App) -> queue.Queue:
        generation_queue = multiprocessing.Manager().Queue()
        generation_queue.put((None, _generate_dispatch, ()))
        for locale in app.project.configuration.locales:
            generation_queue.put((locale, _generate_public, ()))
            generation_queue.put((locale, _generate_openapi, ()))
            for entity_type in app.entity_types:
                if not issubclass(entity_type, UserFacingEntity):
                    continue
                if entity_type in app.project.configuration.entity_types and app.project.configuration.entity_types[entity_type].generate_html_list:
                    generation_queue.put((locale, _generate_entity_type_list_html, (entity_type,)))
                generation_queue.put((locale, _generate_entity_type_list_json, (entity_type,)))
                for entity in app.project.ancestry.entities[entity_type]:
                    if isinstance(entity.id, GeneratedEntityId):
                        continue
                    generation_queue.put((locale, _generate_entity_html, (entity_type, entity.id)))
                    generation_queue.put((locale, _generate_entity_json, (entity_type, entity.id)))
        return generation_queue

    @sync
    async def __call__(self) -> None:
        self._project = pickle.loads(self._pickled_project)
        self._apps: Dict[str | None, App] = {
            None: App(project=self._project),
        }
        for locale in self._project.configuration.locales:
            self._apps[locale] = App(
                project=self._project,
                locale=locale,
            )
        await asyncio.gather(*[
            self._perform_tasks(self._generation_queue)
            for _ in range(0, self._async_concurrency)
        ])

    async def _perform_tasks(self, generation_queue: queue.Queue) -> None:
        while True:
            try:
                locale, task, arguments = generation_queue.get_nowait()
            except queue.Empty:
                return None

            await task(self._apps[locale], self._caller_locale, *arguments)


def create_file(path: Path) -> AsyncContextManager[AsyncTextIOWrapper]:
    path.parent.mkdir(exist_ok=True, parents=True)
    return cast(AsyncContextManager[AsyncTextIOWrapper], aiofiles.open(path, 'w', encoding='utf-8'))


def create_html_resource(path: Path) -> AsyncContextManager[AsyncTextIOWrapper]:
    return create_file(path / 'index.html')


def create_json_resource(path: Path) -> AsyncContextManager[AsyncTextIOWrapper]:
    return create_file(path / 'index.json')


async def _generate_dispatch(
    app: App,
    caller_locale: str,
) -> None:
    await app.dispatcher.dispatch(Generator)(),


async def _generate_public(
        app: App,
        caller_locale: str,
) -> None:
    async for file_path in app.assets.copytree(Path('public') / 'localized', app.www_directory_path):
        await app.renderer.render_file(file_path)


async def _generate_static_public(
        app: App,
        caller_locale: str,
) -> None:
    async for file_path in app.assets.copytree(Path('public') / 'static', app.static_www_directory_path):
        await app.renderer.render_file(file_path)


async def _generate_entity_type_list_html(
    app: App,
    caller_locale: str,
    entity_type: Type[UserFacingEntity],
) -> None:
    entity_type_name_fs = camel_case_to_kebab_case(get_entity_type_name(entity_type))
    entity_type_path = app.www_directory_path / entity_type_name_fs
    template = app.jinja2_environment.negotiate_template([
        f'entity/page-list--{entity_type_name_fs}.html.j2',
        'entity/page-list.html.j2',
    ])
    rendered_html = template.render({
        'page_resource': f'/{entity_type_name_fs}/index.html',
        'entity_type': entity_type,
        'entities': app.project.ancestry.entities[entity_type],
    })
    async with create_html_resource(entity_type_path) as f:
        await f.write(rendered_html)
    locale_label = get_display_name(app.locale, caller_locale)
    getLogger().info(app.localizers[caller_locale]._('Generated the listing page for {entity_type} in {locale}.').format(
        entity_type=entity_type.entity_type_label_plural(app.localizers[caller_locale]),
        locale=locale_label,
    ))


async def _generate_entity_type_list_json(
    app: App,
    caller_locale: str,
    entity_type: Type[UserFacingEntity],
) -> None:
    entity_type_name = get_entity_type_name(entity_type)
    entity_type_name_fs = camel_case_to_kebab_case(get_entity_type_name(entity_type))
    entity_type_path = app.www_directory_path / entity_type_name_fs
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
    async with create_json_resource(entity_type_path) as f:
        await f.write(rendered_json)


async def _generate_entity_html(
    app: App,
    caller_locale: str,
    entity_type: Type[UserFacingEntity],
    entity_id: str,
) -> None:
    entity = app.project.ancestry.entities[entity_type][entity_id]
    entity_type_name_fs = camel_case_to_kebab_case(get_entity_type_name(entity))
    entity_path = app.www_directory_path / entity_type_name_fs / entity.id
    rendered_html = app.jinja2_environment.negotiate_template([
        f'entity/page--{entity_type_name_fs}.html.j2',
        'entity/page.html.j2',
    ]).render({
        'page_resource': entity,
        'entity_type': get_entity_type(entity),
        'entity': entity,
    })
    async with create_html_resource(entity_path) as f:
        await f.write(rendered_html)


async def _generate_entity_json(
    app: App,
    caller_locale: str,
    entity_type: Type[UserFacingEntity],
    entity_id: str,
) -> None:
    entity_type_name_fs = camel_case_to_kebab_case(get_entity_type_name(entity_type))
    entity_path = app.www_directory_path / entity_type_name_fs / entity_id
    rendered_json = json.dumps(app.project.ancestry.entities[entity_type][entity_id], cls=app.json_encoder)
    async with create_json_resource(entity_path) as f:
        await f.write(rendered_json)


async def _generate_openapi(
    app: App,
    reporting_locale: str,
) -> None:
    api_directory_path = app.www_directory_path / 'api'
    api_directory_path.mkdir(exist_ok=True, parents=True)
    rendered_json = json.dumps(Specification(app).build())
    async with create_json_resource(api_directory_path) as f:
        await f.write(rendered_json)


def _get_entity_type_jinja2_name(entity_type_name: str) -> str:
    return camel_case_to_snake_case(entity_type_name).replace('.', '__')
