from __future__ import annotations

import json
import logging
import multiprocessing
import os
import queue
import shutil
import threading
from concurrent.futures import ProcessPoolExecutor, Executor, Future, as_completed
from contextlib import suppress
from ctypes import c_char_p
from multiprocessing.managers import ValueProxy
from pathlib import Path
from types import TracebackType
from typing import cast, AsyncContextManager, Self, Any, ParamSpec, Callable, Concatenate, MutableSequence

import aiofiles
import dill
from aiofiles import os as aiofiles_os
from aiofiles.os import makedirs
from aiofiles.threadpool.text import AsyncTextIOWrapper

from betty.app import App
from betty.asyncio import sync, gather
from betty.locale import get_display_name
from betty.model import get_entity_type_name, UserFacingEntity, Entity, GeneratedEntityId
from betty.model.ancestry import is_public
from betty.openapi import Specification
from betty.serde.dump import DictDump, Dump
from betty.string import camel_case_to_kebab_case, camel_case_to_snake_case
from betty.task import Context

_GenerationProcessPoolTaskP = ParamSpec('_GenerationProcessPoolTaskP')


def getLogger() -> logging.Logger:
    return logging.getLogger(__name__)


class Generator:
    async def generate(self, task_context: GenerationContext) -> None:
        raise NotImplementedError(repr(self))


class GenerationContext(Context):
    def __init__(self, app: App):
        super().__init__()
        self._pickled_app = multiprocessing.Manager().Value(c_char_p, dill.dumps(app))
        self._unpickle_app_lock: threading.Lock = multiprocessing.Manager().Lock()
        self._app: App | None = None

    def __getstate__(self) -> tuple[threading.Lock, MutableSequence[str], ValueProxy[bytes]]:
        return self._claims_lock, self._claimed_task_ids, self._pickled_app

    def __setstate__(self, state: tuple[threading.Lock, MutableSequence[str], ValueProxy[bytes]]) -> None:
        self._claims_lock, self._claimed_task_ids, self._pickled_app = state
        self._unpickle_app_lock = multiprocessing.Manager().Lock()
        self._app = None

    @property
    def app(self) -> App:
        with self._unpickle_app_lock:
            if self._app is None:
                self._app = cast(App, dill.loads(self._pickled_app.value))
        return self._app


class _GenerationProcessPool:
    def __init__(self, app: App, task_context: GenerationContext):
        self._app = app
        self._task_context = task_context
        self._queue = multiprocessing.Manager().Queue()
        self._cancel = multiprocessing.Manager().Event()
        self._finish = multiprocessing.Manager().Event()
        self._executor: Executor | None = None
        self._workers: list[Future[None]] = []

    async def __aenter__(self) -> Self:
        self._executor = ProcessPoolExecutor(max_workers=self._app.concurrency)
        for _ in range(0, self._app.concurrency):
            self._workers.append(self._executor.submit(_GenerationProcessPoolWorker(
                self._queue,
                self._cancel,
                self._finish,
                self._app.concurrency,
                self._task_context,
            )))
        return self

    async def __aexit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None) -> None:
        assert self._executor is not None
        if exc_val is None:
            self._finish.set()
        else:
            self._cancel.set()
        try:
            for worker in as_completed(self._workers):
                worker.result()
        except BaseException:
            self._cancel.set()
            raise
        finally:
            self._executor.shutdown()

    def delegate(
        self,
        task_callable: Callable[Concatenate[GenerationContext, _GenerationProcessPoolTaskP], Any],
        *task_args: _GenerationProcessPoolTaskP.args,
        **task_kwargs: _GenerationProcessPoolTaskP.kwargs,
    ) -> None:
        self._queue.put((task_callable, task_args, task_kwargs))


class _GenerationProcessPoolWorker:
    def __init__(
        self,
        task_queue: queue.Queue[tuple[Callable[Concatenate[GenerationContext, _GenerationProcessPoolTaskP], Any], _GenerationProcessPoolTaskP.args, _GenerationProcessPoolTaskP.kwargs]],
        cancel: threading.Event,
        finish: threading.Event,
        async_concurrency: int,
        task_context: GenerationContext,
    ):
        self._task_queue = task_queue
        self._cancel = cancel
        self._finish = finish
        self._async_concurrency = async_concurrency
        self._context = task_context

    @sync
    async def __call__(self) -> None:
        async with self._context.app:
            await gather(*(
                self._perform_tasks()
                for _ in range(0, self._async_concurrency)
            ))

    async def _perform_tasks(self) -> None:
        while not self._cancel.is_set():
            try:
                task_callable, task_args, task_kwargs = self._task_queue.get_nowait()
            except queue.Empty:
                if self._finish.is_set():
                    return
            else:
                await task_callable(
                    self._context,
                    *task_args,
                    **task_kwargs,
                )


async def generate(app: App) -> None:
    logger = getLogger()
    task_context = GenerationContext(app)

    with suppress(FileNotFoundError):
        shutil.rmtree(app.project.configuration.output_directory_path)
    await aiofiles_os.makedirs(app.project.configuration.output_directory_path, exist_ok=True)
    logger.info(app.localizer._('Generating your site to {output_directory}.').format(output_directory=app.project.configuration.output_directory_path))

    # The static public assets may be overridden depending on the number of locales rendered, so ensure they are
    # generated before anything else.
    await _generate_static_public(app, task_context)

    locales = app.project.configuration.locales

    async with _GenerationProcessPool(app, task_context) as process_pool:
        process_pool.delegate(_generate_dispatch)
        process_pool.delegate(_generate_openapi)

        for locale in locales:
            process_pool.delegate(_generate_public, locale)

        for entity_type in app.entity_types:
            if not issubclass(entity_type, UserFacingEntity):
                continue
            if app.project.configuration.entity_types[entity_type].generate_html_list:
                for locale in locales:
                    process_pool.delegate(_generate_entity_type_list_html, locale, entity_type)
            process_pool.delegate(_generate_entity_type_list_json, entity_type)
            for entity in app.project.ancestry[entity_type]:
                if isinstance(entity.id, GeneratedEntityId):
                    continue

                process_pool.delegate(_generate_entity_json, entity_type, entity.id)
                if is_public(entity):
                    for locale in locales:
                        process_pool.delegate(_generate_entity_html, locale, entity_type, entity.id)

    # Log the generated pages.
    for locale in app.project.configuration.locales:
        locale_label = get_display_name(locale, app.localizer.locale)
        for entity_type in app.entity_types:
            if issubclass(entity_type, UserFacingEntity):
                logger.info(app.localizer._('Generated pages for {count} {entity_type} in {locale}.').format(
                    count=len(app.project.ancestry[entity_type]),
                    entity_type=entity_type.entity_type_label_plural().localize(app.localizer),
                    locale=locale_label,
                ))

    os.chmod(app.project.configuration.output_directory_path, 0o755)
    for directory_path_str, subdirectory_names, file_names in os.walk(app.project.configuration.output_directory_path):
        directory_path = Path(directory_path_str)
        for subdirectory_name in subdirectory_names:
            os.chmod(directory_path / subdirectory_name, 0o755)
        for file_name in file_names:
            os.chmod(directory_path / file_name, 0o644)


async def create_file(path: Path) -> AsyncContextManager[AsyncTextIOWrapper]:
    await makedirs(path.parent, exist_ok=True)
    return cast(AsyncContextManager[AsyncTextIOWrapper], aiofiles.open(path, 'w', encoding='utf-8'))


async def create_html_resource(path: Path) -> AsyncContextManager[AsyncTextIOWrapper]:
    return await create_file(path / 'index.html')


async def create_json_resource(path: Path) -> AsyncContextManager[AsyncTextIOWrapper]:
    return await create_file(path / 'index.json')


async def _generate_dispatch(
    task_context: GenerationContext,
) -> None:
    app = task_context.app
    await app.dispatcher.dispatch(Generator)(task_context),


async def _generate_public(
    task_context: GenerationContext,
    locale: str,
) -> None:
    app = task_context.app
    locale_label = get_display_name(locale, app.localizer.locale)
    getLogger().info(app.localizer._('Generating localized public files in {locale}...').format(
        locale=locale_label,
    ))
    async for file_path in app.assets.copytree(Path('public') / 'localized', app.project.configuration.localize_www_directory_path(locale)):
        await app.renderer.render_file(
            file_path,
            task_context=task_context,
            localizer=app.localizers[locale],
        )


async def _generate_static_public(
    app: App,
    task_context: Context,
) -> None:
    getLogger().info(app.localizer._('Generating static public files...'))
    async for file_path in app.assets.copytree(Path('public') / 'static', app.project.configuration.www_directory_path):
        await app.renderer.render_file(
            file_path,
            task_context=task_context,
        )


async def _generate_entity_type_list_html(
    task_context: GenerationContext,
    locale: str,
    entity_type: type[Entity],
) -> None:
    app = task_context.app
    entity_type_name_fs = camel_case_to_kebab_case(get_entity_type_name(entity_type))
    entity_type_path = app.project.configuration.localize_www_directory_path(locale) / entity_type_name_fs
    template = app.jinja2_environment.negotiate_template([
        f'entity/page-list--{entity_type_name_fs}.html.j2',
        'entity/page-list.html.j2',
    ])
    rendered_html = await template.render_async(
        task_context=task_context,
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
    task_context: GenerationContext,
    entity_type: type[Entity],
) -> None:
    app = task_context.app
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
    task_context: GenerationContext,
    locale: str,
    entity_type: type[Entity],
    entity_id: str,
) -> None:
    app = task_context.app
    entity = app.project.ancestry[entity_type][entity_id]
    entity_type_name_fs = camel_case_to_kebab_case(get_entity_type_name(entity))
    entity_path = app.project.configuration.localize_www_directory_path(locale) / entity_type_name_fs / entity.id
    rendered_html = await app.jinja2_environment.negotiate_template([
        f'entity/page--{entity_type_name_fs}.html.j2',
        'entity/page.html.j2',
    ]).render_async(
        task_context=task_context,
        localizer=app.localizers[locale],
        page_resource=entity,
        entity_type=entity.type,
        entity=entity,
    )
    async with await create_html_resource(entity_path) as f:
        await f.write(rendered_html)


async def _generate_entity_json(
    task_context: GenerationContext,
    entity_type: type[Entity],
    entity_id: str,
) -> None:
    app = task_context.app
    entity_type_name_fs = camel_case_to_kebab_case(get_entity_type_name(entity_type))
    entity_path = app.project.configuration.www_directory_path / entity_type_name_fs / entity_id
    rendered_json = json.dumps(app.project.ancestry[entity_type][entity_id], cls=app.json_encoder)
    async with await create_json_resource(entity_path) as f:
        await f.write(rendered_json)


async def _generate_openapi(
    task_context: GenerationContext,
) -> None:
    app = task_context.app
    getLogger().info(app.localizer._('Generating OpenAPI specification...'))
    api_directory_path = app.project.configuration.www_directory_path / 'api'
    rendered_json = json.dumps(Specification(app).build())
    async with await create_json_resource(api_directory_path) as f:
        await f.write(rendered_json)


def _get_entity_type_jinja2_name(entity_type_name: str) -> str:
    return camel_case_to_snake_case(entity_type_name).replace('.', '__')
