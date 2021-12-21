from __future__ import annotations

import asyncio
import json
import logging
import multiprocessing
import os
import queue
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, cast, AsyncContextManager, List, Type, Mapping, Dict

import aiofiles
from aiofiles import os as aiofiles_os
from aiofiles.threadpool.text import AsyncTextIOWrapper
import dill as pickle

from betty.app import App
from betty.asyncio import sync
from betty.json import JSONEncoder
from betty.locale import get_display_name
from betty.model import get_entity_type_name, UserFacingEntity, get_entity_type, GeneratedEntityId
from betty.openapi import build_specification
from betty.string import camel_case_to_kebab_case, camel_case_to_snake_case

if TYPE_CHECKING:
    from betty.builtins import _


def getLogger() -> logging.Logger:
    return logging.getLogger(__name__)


class Generator:
    async def generate(self) -> None:
        raise NotImplementedError


async def generate(app: App) -> None:
    shutil.rmtree(app.project.configuration.output_directory_path, ignore_errors=True)
    await aiofiles_os.makedirs(app.project.configuration.output_directory_path)
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
        localized_queues: Mapping[str | None, multiprocessing.Queue],
        pickled_project: bytes,
    ):
        self._localized_queues = localized_queues
        self._pickled_project = pickled_project

    @classmethod
    async def generate(cls, app: App) -> None:
        localized_queues = cls._build_queues(app)
        pickled_project = pickle.dumps(app.project)
        await asyncio.gather(*[
            app.do_in_process(cls(localized_queues, pickled_project))
            for _ in range(0, app.concurrency)
        ])

        # Log the generated pages.
        logger = getLogger()
        for locale_configuration in app.project.configuration.locales:
            locale = locale_configuration.locale
            locale_label = get_display_name(locale, app.configuration.locale or 'en-US')
            for entity_type in app.entity_types:
                if issubclass(entity_type, UserFacingEntity):
                    logger.info(_('Generated pages for {count} {entity_type} in {locale}.').format(
                        count=len(app.project.ancestry.entities[entity_type]),
                        entity_type=entity_type.entity_type_label_plural(),
                        locale=locale_label,
                    ))

    @classmethod
    def _build_queues(cls, app: App) -> Mapping[str | None, multiprocessing.Queue]:
        localized_queues: Dict[str | None, multiprocessing.Queue] = {
            None: multiprocessing.Manager().Queue(),  # type: ignore[dict-item]
        }
        localized_queues[None].put((cls._generate_dispatch, ()))
        localized_queues[None].put((cls._generate_static_public, ()))
        for locale_configuration in app.project.configuration.locales:
            locale = locale_configuration.locale
            localized_queues[locale] = multiprocessing.Manager().Queue()  # type: ignore[assignment]
            localized_queues[locale].put((cls._generate_public, ()))
            localized_queues[locale].put((cls._generate_openapi, ()))
            for entity_type in app.entity_types:
                if not issubclass(entity_type, UserFacingEntity):
                    continue
                if entity_type in app.project.configuration.entity_types and app.project.configuration.entity_types[entity_type].generate_html_list:
                    localized_queues[locale].put((cls._generate_entity_type_list_html, (entity_type,)))
                localized_queues[locale].put((cls._generate_entity_type_list_json, (entity_type,)))
                for entity in app.project.ancestry.entities[entity_type]:
                    if isinstance(entity.id, GeneratedEntityId):
                        continue
                    localized_queues[locale].put((cls._generate_entity_html, (entity_type, entity.id)))
                    localized_queues[locale].put((cls._generate_entity_json, (entity_type, entity.id)))
        return localized_queues

    @sync
    async def __call__(self) -> None:
        self._app = App(project=pickle.loads(self._pickled_project))
        with self._app:
            for locale, localized_queue in self._localized_queues.items():
                localized_queue_empty = False
                while not localized_queue_empty:
                    if locale is None:
                        localized_queue_empty = await self._perform_tasks(localized_queue)
                    else:
                        with self._app.acquire_locale(locale):
                            localized_queue_empty = await self._perform_tasks(localized_queue)

    async def _perform_tasks(self, localized_queue: multiprocessing.queues.Queue) -> bool:
        return True in await asyncio.gather(*[
            self._perform_task(localized_queue)
            for _ in range(0, self._app.concurrency)
        ])

    async def _perform_task(self, localized_queue: multiprocessing.queues.Queue) -> bool:
        try:
            method, arguments = localized_queue.get_nowait()
        except queue.Empty:
            return True
        await method(self, *arguments)
        return False

    async def _generate_dispatch(self):
        await self._app.dispatcher.dispatch(Generator)(),

    async def _generate_public(self):
        async for file_path in self._app.assets.copytree(Path('public') / 'localized', self._app.www_directory_path):
            await self._app.renderer.render_file(file_path)

    async def _generate_static_public(self):
        async for file_path in self._app.assets.copytree(Path('public') / 'static', self._app.static_www_directory_path):
            await self._app.renderer.render_file(file_path)

    async def _generate_entity_type_list_html(
        self,
        entity_type: Type[UserFacingEntity],
    ) -> None:
        entity_type_name_fs = camel_case_to_kebab_case(get_entity_type_name(entity_type))
        entity_type_path = self._app.www_directory_path / entity_type_name_fs
        template = self._app.jinja2_environment.negotiate_template([
            f'entity/page-list--{entity_type_name_fs}.html.j2',
            'entity/page-list.html.j2',
        ])
        rendered_html = template.render({
            'page_resource': f'/{entity_type_name_fs}/index.html',
            'entity_type': entity_type,
            'entities': self._app.project.ancestry.entities[entity_type],
        })
        async with _create_html_resource(entity_type_path) as f:
            await f.write(rendered_html)
        locale_label = get_display_name(self._app.locale, self._app.configuration.locale or 'en-US')
        getLogger().debug(_('Generated the listing HTML page for {entity_type} entities in {locale}.').format(
            entity_type=entity_type.entity_type_label_plural(),
            locale=locale_label,
        ))

    async def _generate_entity_type_list_json(
        self,
        entity_type: Type[UserFacingEntity],
    ) -> None:
        entity_type_name = get_entity_type_name(entity_type)
        entity_type_name_fs = camel_case_to_kebab_case(get_entity_type_name(entity_type))
        entity_type_path = self._app.www_directory_path / entity_type_name_fs
        data = {
            '$schema': self._app.static_url_generator.generate('schema.json#/definitions/%sCollection' % entity_type_name, absolute=True),
            'collection': []
        }
        for entity in self._app.project.ancestry.entities[entity_type]:
            cast(List[str], data['collection']).append(
                self._app.url_generator.generate(
                    entity,
                    'application/json',
                    absolute=True,
                ))
        rendered_json = json.dumps(data)
        async with _create_json_resource(entity_type_path) as f:
            await f.write(rendered_json)

    async def _generate_entity_html(
        self,
        entity_type: Type[UserFacingEntity],
        entity_id: str,
    ) -> None:
        entity = self._app.project.ancestry.entities[entity_type][entity_id]
        entity_type_name_fs = camel_case_to_kebab_case(get_entity_type_name(entity))
        entity_path = self._app.www_directory_path / entity_type_name_fs / entity.id
        rendered_html = self._app.jinja2_environment.negotiate_template([
            f'entity/page--{entity_type_name_fs}.html.j2',
            'entity/page.html.j2',
        ]).render({
            'page_resource': entity,
            'entity_type': get_entity_type(entity),
            'entity': entity,
        })
        async with _create_html_resource(entity_path) as f:
            await f.write(rendered_html)

    async def _generate_entity_json(
        self,
        entity_type: Type[UserFacingEntity],
        entity_id: str,
    ) -> None:
        entity_type_name_fs = camel_case_to_kebab_case(get_entity_type_name(entity_type))
        entity_path = self._app.www_directory_path / entity_type_name_fs / entity_id
        rendered_json = json.dumps(self._app.project.ancestry.entities[entity_type][entity_id], cls=JSONEncoder.get_factory(self._app))
        async with _create_json_resource(entity_path) as f:
            await f.write(rendered_json)

    async def _generate_openapi(self) -> None:
        api_directory_path = self._app.www_directory_path / 'api'
        api_directory_path.mkdir(exist_ok=True, parents=True)
        rendered_json = json.dumps(build_specification(self._app))
        async with _create_json_resource(api_directory_path) as f:
            await f.write(rendered_json)


def _create_file(path: Path) -> AsyncContextManager[AsyncTextIOWrapper]:
    path.parent.mkdir(exist_ok=True, parents=True)
    return cast(AsyncContextManager[AsyncTextIOWrapper], aiofiles.open(path, 'w', encoding='utf-8'))


def _create_html_resource(path: Path) -> AsyncContextManager[AsyncTextIOWrapper]:
    return _create_file(path / 'index.html')


def _create_json_resource(path: Path) -> AsyncContextManager[AsyncTextIOWrapper]:
    return _create_file(path / 'index.json')


def _get_entity_type_jinja2_name(entity_type_name: str) -> str:
    return camel_case_to_snake_case(entity_type_name).replace('.', '__')
