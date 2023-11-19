from __future__ import annotations

import json
import logging
import multiprocessing
import os
import shutil
from contextlib import suppress, AsyncExitStack
from pathlib import Path
from typing import cast, AsyncContextManager, Concatenate

import aiofiles
import dill
from aiofiles import os as aiofiles_os
from aiofiles.os import makedirs
from aiofiles.threadpool.text import AsyncTextIOWrapper

from betty.app import App
from betty.asyncio import gather
from betty.locale import get_display_name
from betty.model import get_entity_type_name, UserFacingEntity, Entity
from betty.openapi import Specification
from betty.serde.dump import DictDump, Dump
from betty.string import camel_case_to_kebab_case, camel_case_to_snake_case
from betty.task import _TaskBatch, TaskP

GenerationTaskP = Concatenate[App, TaskP]


def getLogger() -> logging.Logger:
    return logging.getLogger(__name__)


class Generator:
    async def generate(self, batch: _TaskBatch[GenerationTaskBatchContext], app: App) -> None:
        raise NotImplementedError(repr(self))


class GenerationTaskBatchContext:
    _app: App

    def __init__(self, pickled_app: bytes, app_locale: str | None):
        self._pickled_app = pickled_app
        self._app_locale = app_locale
        self._unpickle_lock = multiprocessing.Manager().Lock()

    async def app(self) -> App:
        try:
            return self._app
        except AttributeError:
            with self._unpickle_lock:
                app = cast(App, dill.loads(self._pickled_app))
                if self._app_locale:
                    app.locale = self._app_locale
                self._app = app
                return app


async def generate(app: App) -> None:
    logger = getLogger()

    with suppress(FileNotFoundError):
        shutil.rmtree(app.project.configuration.output_directory_path)
    await aiofiles_os.makedirs(app.project.configuration.output_directory_path, exist_ok=True)
    logger.info(app.localizer._('Generating your site to {output_directory}.').format(output_directory=app.project.configuration.output_directory_path))

    # The static public assets may be overridden depending on the number of locales rendered, so ensure they are
    # generated before anything else.
    # @todo Are we sure this is uses the default language?
    await _generate_static_public(app)

    # @todo Now, how do we ensure that Jinja2 filters have access to this batch?
    # @todo Because at any time, App may be serving multiple batches besides the manager's own
    # @todo
    pickled_app = dill.dumps(app)
    localized_process_batches: dict[str | None, _TaskBatch[GenerationTaskBatchContext]] = {}
    locales = app.project.configuration.locales

    # @todo Exit stacks exit the contained contexts in LIFO order, NOT concurrently!
    # @todo Do we lose time waiting? Or does it not matter?
    # @todo Because the group of batches is not done until all batches are done.
    # @todo And if we have to wait for one batch to finish while the others are finished already
    # @todo we would have had to wait for this one batch anyway
    # @todo
    # @todo Main concern is error handling, where we want errors as soon as possible
    # @todo
    # @todo
    # @todo
    async with AsyncExitStack() as batch_stack:
        thread_batch = app.thread_pool.batch()
        print('thread_batch')
        print(thread_batch)

        localized_process_batches[None] = app.process_pool.batch(GenerationTaskBatchContext(pickled_app, None))
        print('localized_process_batches[None]')
        print(localized_process_batches[None])

        # @todo Are we indeed passing on an unlocalized app?
        # localized_process_batches[None].delegate(Task(_generate_dispatch))
        # await _generate_openapi(localized_process_batches[None])
        localized_process_batches[None].delegate(_generate_openapi)

        for locale in locales:
            localized_process_batches[locale] = app.process_pool.batch(GenerationTaskBatchContext(pickled_app, locale))
            print('localized_process_batches[locale]')
            print(localized_process_batches[locale])

            # localized_process_batches[locale].delegate(Task(_generate_public))

        # for entity_type in app.entity_types:
        #     if not issubclass(entity_type, UserFacingEntity):
        #         continue
        #     if app.project.configuration.entity_types[entity_type].generate_html_list:
        #         for locale in locales:
        #             batches[locale].to_thread(Task(_generate_entity_type_list_html, entity_type))
        #     batches[None].to_thread(Task(_generate_entity_type_list_json, entity_type))
        #     for entity in app.project.ancestry[entity_type]:
        #         if isinstance(entity.id, GeneratedEntityId):
        #             continue
        #
        #         batches[None].to_thread(Task(_generate_entity_json, entity_type, entity.id))
        #         if is_public(entity):
        #             for locale in locales:
        #                 batches[locale].to_thread(Task(_generate_entity_html, entity_type, entity.id))

        print('ENTERING BATCHES')
        await gather(*(
            batch_stack.enter_async_context(batch)  # type: ignore[arg-type]
            for batch
            in [
                thread_batch,
                *localized_process_batches.values(),
            ]
        ))
        print('EXITING BATCHES')
    print('EXITED BATCHES')

    # Log the generated pages.
    for locale in app.project.configuration.locales:
        locale_label = get_display_name(locale, app.localizer.locale)
        for entity_type in app.entity_types:
            if issubclass(entity_type, UserFacingEntity):
                logger.info(app.localizer._('Generated pages for {count} {entity_type} in {locale}.').format(
                    count=len(app.project.ancestry[entity_type]),
                    entity_type=entity_type.entity_type_label_plural(app.localizer),
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
    batch: _TaskBatch[GenerationTaskBatchContext],
) -> None:
    async with await batch.context.app() as app:
        await app.dispatcher.dispatch(Generator)(batch, app),


async def _generate_public(
    batch: _TaskBatch[GenerationTaskBatchContext],
) -> None:
    print('GENERATE PUBLIC')
    async with await batch.context.app() as app:
        locale_label = get_display_name(app.locale, batch.logging_locale)
        getLogger().info(app.localizers[batch.logging_locale]._('Generating localized public files in {locale}...').format(
            locale=locale_label,
        ))
        async for file_path in app.assets.copytree(Path('public') / 'localized', app.www_directory_path):
            await app.renderer.render_file(file_path)


async def _generate_static_public(
    app: App,
) -> None:
    print('GENERATE STATIC PUBLIC')
    getLogger().info(app.localizer._('Generating static public files...'))
    async for file_path in app.assets.copytree(Path('public') / 'static', app.static_www_directory_path):
        await app.renderer.render_file(file_path)


async def _generate_entity_type_list_html(
    batch: _TaskBatch[GenerationTaskBatchContext],
    entity_type: type[Entity],
) -> None:
    async with await batch.context.app() as app:
        entity_type_name_fs = camel_case_to_kebab_case(get_entity_type_name(entity_type))
        entity_type_path = app.www_directory_path / entity_type_name_fs
        template = app.jinja2_environment.negotiate_template([
            f'entity/page-list--{entity_type_name_fs}.html.j2',
            'entity/page-list.html.j2',
        ])
        rendered_html = template.render(
            page_resource=f'/{entity_type_name_fs}/index.html',
            entity_type=entity_type,
            entities=app.project.ancestry[entity_type],
        )
        async with await create_html_resource(entity_type_path) as f:
            await f.write(rendered_html)
        locale_label = get_display_name(app.locale, batch.logging_locale)
        getLogger().info(app.localizers[batch.logging_locale]._('Generated the listing page for {entity_type} in {locale}.').format(
            entity_type=entity_type.entity_type_label_plural(app.localizers[batch.logging_locale]),
            locale=locale_label,
        ))


async def _generate_entity_type_list_json(
    batch: _TaskBatch[GenerationTaskBatchContext],
    entity_type: type[Entity],
) -> None:
    async with await batch.context.app() as app:
        entity_type_name = get_entity_type_name(entity_type)
        entity_type_name_fs = camel_case_to_kebab_case(get_entity_type_name(entity_type))
        entity_type_path = app.static_www_directory_path / entity_type_name_fs
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
    batch: _TaskBatch[GenerationTaskBatchContext],
    entity_type: type[Entity],
    entity_id: str,
) -> None:
    async with await batch.context.app() as app:
        entity = app.project.ancestry[entity_type][entity_id]
        entity_type_name_fs = camel_case_to_kebab_case(get_entity_type_name(entity))
        entity_path = app.www_directory_path / entity_type_name_fs / entity.id
        rendered_html = app.jinja2_environment.negotiate_template([
            f'entity/page--{entity_type_name_fs}.html.j2',
            'entity/page.html.j2',
        ]).render(
            page_resource=entity,
            entity_type=entity.type,
            entity=entity,
        )
        async with await create_html_resource(entity_path) as f:
            await f.write(rendered_html)


async def _generate_entity_json(
    batch: _TaskBatch[GenerationTaskBatchContext],
    entity_type: type[Entity],
    entity_id: str,
) -> None:
    async with await batch.context.app() as app:
        entity_type_name_fs = camel_case_to_kebab_case(get_entity_type_name(entity_type))
        entity_path = app.static_www_directory_path / entity_type_name_fs / entity_id
        rendered_json = json.dumps(app.project.ancestry[entity_type][entity_id], cls=app.json_encoder)
        async with await create_json_resource(entity_path) as f:
            await f.write(rendered_json)


async def _generate_openapi(
    batch: _TaskBatch[GenerationTaskBatchContext],
) -> None:
    print('GENERATE OPENAPI')
    async with await batch.context.app() as app:
        getLogger().info(app.localizers[batch.logging_locale]._('Generating OpenAPI specification...'))
        api_directory_path = app.www_directory_path / 'api'
        print('GENERATE OPENAPI RENDER JSON')
        rendered_json = json.dumps(Specification(app).build())
    print('GENERATE OPENAPI MAKE DIRS')
    await makedirs(str(api_directory_path))
    print('GENERATE OPENAPI CREATE JSON FILE')
    async with await create_json_resource(api_directory_path) as f:
        print('GENERATE OPENAPI WRITE JSON FILE')
        await f.write(rendered_json)
    print('GENERATE OPENAPI DONE')


def _get_entity_type_jinja2_name(entity_type_name: str) -> str:
    return camel_case_to_snake_case(entity_type_name).replace('.', '__')
