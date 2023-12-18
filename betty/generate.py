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
from typing import cast, AsyncContextManager, Callable, Generic, Any, Awaitable, ParamSpec, Concatenate

import aiofiles
import dill
from aiofiles import os as aiofiles_os
from aiofiles.os import makedirs
from aiofiles.threadpool.text import AsyncTextIOWrapper

from betty.app import App
from betty.asyncio import sync, gather
from betty.locale import get_display_name
from betty.model import get_entity_type_name, UserFacingEntity, GeneratedEntityId, Entity
from betty.model.ancestry import is_public
from betty.openapi import Specification
from betty.project import Project
from betty.serde.dump import DictDump, Dump
from betty.string import camel_case_to_kebab_case, camel_case_to_snake_case

P = ParamSpec('P')


def getLogger() -> logging.Logger:
    return logging.getLogger(__name__)


class Generator:
    async def generate(self) -> None:
        raise NotImplementedError(repr(self))


async def generate(app: App) -> None:
    async with app:
        with suppress(FileNotFoundError):
            shutil.rmtree(app.project.configuration.output_directory_path)
        await aiofiles_os.makedirs(app.project.configuration.output_directory_path, exist_ok=True)
        logging.getLogger().info(app.localizer._('Generating your site to {output_directory}.').format(
            output_directory=app.project.configuration.output_directory_path,
        ))
        await _ConcurrentGenerator.generate(app)
        os.chmod(app.project.configuration.output_directory_path, 0o755)
        for directory_path_str, subdirectory_names, file_names in os.walk(app.project.configuration.output_directory_path):
            directory_path = Path(directory_path_str)
            for subdirectory_name in subdirectory_names:
                os.chmod(directory_path / subdirectory_name, 0o755)
            for file_name in file_names:
                os.chmod(directory_path / file_name, 0o644)


class _GenerationTask(Generic[P]):
    def __init__(
        self,
        locale: str,
        callable: Callable[Concatenate[App, str, P], Awaitable[None]],
        *args: P.args,
        **kwargs: P.kwargs,
    ):
        self.locale = locale
        self.callable = callable
        self.args = args
        self.kwargs = kwargs


class _ConcurrentGenerator:
    def __init__(
        self,
        generation_queue: queue.Queue[_GenerationTask[Any]],
        pickled_project: bytes,
        async_concurrency: int,
        generation_locales: set[str],
    ):
        self._generation_queue = generation_queue
        self._pickled_project = pickled_project
        self._project: Project
        self._async_concurrency = async_concurrency
        self._generation_locales = generation_locales

    @classmethod
    async def generate(cls, app: App) -> None:
        # The static public assets may be overridden depending on the number of locales rendered, so ensure they are
        # generated before anything else.
        await _generate_static_public(app)
        generation_queue = cls._build_generation_queue(app)

        pickled_project = dill.dumps(app.project)
        await asyncio.gather(*[
            app.wait_for_process(cls(
                generation_queue,
                pickled_project,
                app.async_concurrency,
                set(app.project.configuration.locales),
            ))
            for _ in range(0, app.concurrency)
        ])

        # Log the generated pages.
        logger = getLogger()
        for locale in app.project.configuration.locales:
            locale_label = get_display_name(locale, app.localizer.locale)
            for entity_type in app.entity_types:
                if issubclass(entity_type, UserFacingEntity):
                    logger.info(app.localizer._('Generated pages for {count} {entity_type} in {locale}.').format(
                        count=len(app.project.ancestry[entity_type]),
                        entity_type=entity_type.entity_type_label_plural().localize(app.localizer),
                        locale=locale_label,
                    ))

    @classmethod
    def _build_generation_queue(cls, app: App) -> queue.Queue[_GenerationTask[Any]]:
        locales = app.project.configuration.locales
        generation_queue: queue.Queue[_GenerationTask[Any]] = multiprocessing.Manager().Queue()
        generation_queue.put(_GenerationTask(locales.default.locale, _generate_dispatch))
        generation_queue.put(_GenerationTask(locales.default.locale, _generate_openapi))
        for locale in locales:
            generation_queue.put(_GenerationTask(locale, _generate_public))
        for entity_type in app.entity_types:
            if not issubclass(entity_type, UserFacingEntity):
                continue
            if app.project.configuration.entity_types[entity_type].generate_html_list:
                for locale in locales:
                    generation_queue.put(_GenerationTask(locale, _generate_entity_type_list_html, entity_type))
            generation_queue.put(_GenerationTask(locales.default.locale, _generate_entity_type_list_json, entity_type))
            for entity in app.project.ancestry[entity_type]:
                if isinstance(entity.id, GeneratedEntityId):
                    continue

                generation_queue.put(_GenerationTask(locales.default.locale, _generate_entity_json, entity_type, entity.id))
                if is_public(entity):
                    for locale in locales:
                        generation_queue.put(_GenerationTask(locale, _generate_entity_html, entity_type, entity.id))
        return generation_queue

    @sync
    async def __call__(self) -> None:
        self._app = App(
            project=dill.loads(self._pickled_project),
        )
        await gather(*(
            self._perform_tasks(self._generation_queue)
            for _
            in range(0, self._async_concurrency)
        ))

    async def _perform_tasks(self, generation_queue: queue.Queue[_GenerationTask[Any]]) -> None:
        while True:
            try:
                task = generation_queue.get_nowait()
            except queue.Empty:
                return None

            await task.callable(
                self._app,
                task.locale,
                *task.args,
                **task.kwargs,
            )


async def create_file(path: Path) -> AsyncContextManager[AsyncTextIOWrapper]:
    await makedirs(path.parent, exist_ok=True)
    return cast(AsyncContextManager[AsyncTextIOWrapper], aiofiles.open(path, 'w', encoding='utf-8'))


async def create_html_resource(path: Path) -> AsyncContextManager[AsyncTextIOWrapper]:
    return await create_file(path / 'index.html')


async def create_json_resource(path: Path) -> AsyncContextManager[AsyncTextIOWrapper]:
    return await create_file(path / 'index.json')


async def _generate_dispatch(
    app: App,
    locale: str,
) -> None:
    await app.dispatcher.dispatch(Generator)(),


async def _generate_public(
        app: App,
        locale: str,
) -> None:
    async for file_path in app.assets.copytree(Path('public') / 'localized', app.project.configuration.localize_www_directory_path(locale)):
        await app.renderer.render_file(file_path, localizer=app.localizers[locale])


async def _generate_static_public(
        app: App,
) -> None:
    async for file_path in app.assets.copytree(Path('public') / 'static', app.project.configuration.www_directory_path):
        await app.renderer.render_file(file_path)


async def _generate_entity_type_list_html(
    app: App,
    locale: str,
    entity_type: type[Entity],
) -> None:
    entity_type_name_fs = camel_case_to_kebab_case(get_entity_type_name(entity_type))
    entity_type_path = app.project.configuration.localize_www_directory_path(locale) / entity_type_name_fs
    template = app.jinja2_environment.negotiate_template([
        f'entity/page-list--{entity_type_name_fs}.html.j2',
        'entity/page-list.html.j2',
    ])
    rendered_html = template.render(
        localizer=app.localizers[locale],
        page_resource=f'/{entity_type_name_fs}/index.html',
        entity_type=entity_type,
        entities=app.project.ancestry[entity_type],
    )
    async with await create_html_resource(entity_type_path) as f:
        await f.write(rendered_html)
    locale_label = get_display_name(locale, app.localizer.locale)
    getLogger().info(app.localizer._('Generated the listing page for {entity_type} in {locale}.').format(
        entity_type=entity_type.entity_type_label_plural().localize(app.localizer),
        locale=locale_label,
    ))


async def _generate_entity_type_list_json(
    app: App,
    locale: str,
    entity_type: type[Entity],
) -> None:
    entity_type_name = get_entity_type_name(entity_type)
    entity_type_name_fs = camel_case_to_kebab_case(get_entity_type_name(entity_type))
    entity_type_path = app.project.configuration.www_directory_path / entity_type_name_fs
    data: DictDump[Dump] = {
        '$schema': app.static_url_generator.generate('schema.json#/definitions/%sCollection' % entity_type_name, absolute=True),
        'collection': []
    }
    for entity in app.project.ancestry[entity_type]:
        cast(list[str], data['collection']).append(
            app.url_generator.generate(
                entity,
                'application/json',
                absolute=True,
            ))
    rendered_json = json.dumps(data)
    async with await create_json_resource(entity_type_path) as f:
        await f.write(rendered_json)


async def _generate_entity_html(
    app: App,
    locale: str,
    entity_type: type[Entity],
    entity_id: str,
) -> None:
    entity = app.project.ancestry[entity_type][entity_id]
    entity_type_name_fs = camel_case_to_kebab_case(get_entity_type_name(entity))
    entity_path = app.project.configuration.localize_www_directory_path(locale) / entity_type_name_fs / entity.id
    rendered_html = app.jinja2_environment.negotiate_template([
        f'entity/page--{entity_type_name_fs}.html.j2',
        'entity/page.html.j2',
    ]).render(
        localizer=app.localizers[locale],
        page_resource=entity,
        entity_type=entity.type,
        entity=entity,
    )
    async with await create_html_resource(entity_path) as f:
        await f.write(rendered_html)


async def _generate_entity_json(
    app: App,
    locale: str,
    entity_type: type[Entity],
    entity_id: str,
) -> None:
    entity_type_name_fs = camel_case_to_kebab_case(get_entity_type_name(entity_type))
    entity_path = app.project.configuration.www_directory_path / entity_type_name_fs / entity_id
    rendered_json = json.dumps(app.project.ancestry[entity_type][entity_id], cls=app.json_encoder)
    async with await create_json_resource(entity_path) as f:
        await f.write(rendered_json)


async def _generate_openapi(
    app: App,
    locale: str,
) -> None:
    api_directory_path = app.project.configuration.www_directory_path / 'api'
    await makedirs(api_directory_path, exist_ok=True)
    rendered_json = json.dumps(Specification(app, locale).build(), cls=app.json_encoder)
    async with await create_json_resource(api_directory_path) as f:
        await f.write(rendered_json)


def _get_entity_type_jinja2_name(entity_type_name: str) -> str:
    return camel_case_to_snake_case(entity_type_name).replace('.', '__')
