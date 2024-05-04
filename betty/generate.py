"""
Provide the Generation API.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import shutil
from asyncio import create_task, Task, as_completed, Semaphore, CancelledError, sleep
from collections.abc import AsyncIterator
from contextlib import suppress
from math import floor
from pathlib import Path
from typing import cast, AsyncContextManager, ParamSpec, Callable, Awaitable, Sequence

import aiofiles
from aiofiles.os import makedirs
from aiofiles.threadpool.text import AsyncTextIOWrapper

from betty.app import App
from betty.job import Context
from betty.json.linked_data import LinkedDataDumpable
from betty.json.schema import Schema
from betty.locale import get_display_name
from betty.model import (
    get_entity_type_name,
    UserFacingEntity,
    Entity,
    GeneratedEntityId,
)
from betty.model.ancestry import is_public
from betty.openapi import Specification
from betty.serde.dump import DictDump, Dump
from betty.string import (
    camel_case_to_kebab_case,
    camel_case_to_snake_case,
    upper_camel_case_to_lower_camel_case,
)
from betty.warnings import deprecated


@deprecated(
    "This function is deprecated as of Betty 0.3.2, and will be removed in Betty 0.4.x. Instead, use `logging.logging.getLogger(__name__)`."
)
def getLogger() -> logging.Logger:
    """
    Get the site generation logger.
    """
    return logging.getLogger(__name__)


class Generator:
    async def generate(self, job_context: GenerationContext) -> None:
        raise NotImplementedError(repr(self))


class GenerationContext(Context):
    def __init__(self, app: App):
        super().__init__()
        self._app = app

    @property
    def app(self) -> App:
        return self._app


async def generate(app: App) -> None:
    """
    Generate a new site.
    """
    logger = logging.getLogger(__name__)
    job_context = GenerationContext(app)

    logger.info(
        app.localizer._("Generating your site to {output_directory}.").format(
            output_directory=app.project.configuration.output_directory_path
        )
    )
    with suppress(FileNotFoundError):
        await asyncio.to_thread(
            shutil.rmtree, app.project.configuration.output_directory_path
        )
    await makedirs(app.project.configuration.output_directory_path, exist_ok=True)

    # The static public assets may be overridden depending on the number of locales rendered, so ensure they are
    # generated before anything else.
    await _generate_static_public(app, job_context)

    jobs = [job async for job in _run_jobs(app, job_context)]
    log_job = create_task(_log_jobs_forever(app, jobs))
    for completed_job in as_completed(jobs):
        await completed_job
    log_job.cancel()
    await _log_jobs(app, jobs)

    os.chmod(app.project.configuration.output_directory_path, 0o755)
    for directory_path_str, subdirectory_names, file_names in os.walk(
        app.project.configuration.output_directory_path
    ):
        directory_path = Path(directory_path_str)
        for subdirectory_name in subdirectory_names:
            os.chmod(directory_path / subdirectory_name, 0o755)
        for file_name in file_names:
            os.chmod(directory_path / file_name, 0o644)


async def _log_jobs(app: App, jobs: Sequence[Task[None]]) -> None:
    total_job_count = len(jobs)
    completed_job_count = len([job for job in jobs if job.done()])
    logging.getLogger(__name__).info(
        app.localizer._(
            "Generated {completed_job_count} out of {total_job_count} items ({completed_job_percentage}%)."
        ).format(
            completed_job_count=completed_job_count,
            total_job_count=total_job_count,
            completed_job_percentage=floor(
                completed_job_count / (total_job_count / 100)
            ),
        )
    )


async def _log_jobs_forever(app: App, jobs: Sequence[Task[None]]) -> None:
    with suppress(CancelledError):
        while True:
            await _log_jobs(app, jobs)
            await sleep(5)


_JobP = ParamSpec("_JobP")


def _run_job(
    semaphore: Semaphore,
    f: Callable[_JobP, Awaitable[None]],
    *args: _JobP.args,
    **kwargs: _JobP.kwargs,
) -> Task[None]:
    async def _job():
        async with semaphore:
            await f(*args, **kwargs)

    return create_task(_job())


async def _run_jobs(
    app: App, job_context: GenerationContext
) -> AsyncIterator[Task[None]]:
    semaphore = Semaphore(512)
    yield _run_job(semaphore, _generate_dispatch, job_context)
    yield _run_job(semaphore, _generate_sitemap, job_context)
    yield _run_job(semaphore, _generate_json_schema, job_context)
    yield _run_job(semaphore, _generate_openapi, job_context)

    locales = app.project.configuration.locales

    for locale in locales:
        yield _run_job(semaphore, _generate_public, job_context, locale)

    for entity_type in app.entity_types:
        if not issubclass(entity_type, UserFacingEntity):
            continue
        if app.project.configuration.entity_types[entity_type].generate_html_list:
            for locale in locales:
                yield _run_job(
                    semaphore,
                    _generate_entity_type_list_html,
                    job_context,
                    locale,
                    entity_type,
                )
        yield _run_job(
            semaphore, _generate_entity_type_list_json, job_context, entity_type
        )
        for entity in app.project.ancestry[entity_type]:
            if isinstance(entity.id, GeneratedEntityId):
                continue

            yield _run_job(
                semaphore, _generate_entity_json, job_context, entity_type, entity.id
            )
            if is_public(entity):
                for locale in locales:
                    yield _run_job(
                        semaphore,
                        _generate_entity_html,
                        job_context,
                        locale,
                        entity_type,
                        entity.id,
                    )


async def create_file(path: Path) -> AsyncContextManager[AsyncTextIOWrapper]:
    """
    Create the file for a resource.
    """
    await makedirs(path.parent, exist_ok=True)
    return cast(
        AsyncContextManager[AsyncTextIOWrapper],
        aiofiles.open(path, "w", encoding="utf-8"),
    )


async def create_html_resource(path: Path) -> AsyncContextManager[AsyncTextIOWrapper]:
    """
    Create the file for an HTML resource.
    """
    return await create_file(path / "index.html")


async def create_json_resource(path: Path) -> AsyncContextManager[AsyncTextIOWrapper]:
    """
    Create the file for a JSON resource.
    """
    return await create_file(path / "index.json")


async def _generate_dispatch(
    job_context: GenerationContext,
) -> None:
    app = job_context.app
    await app.dispatcher.dispatch(Generator)(job_context)


async def _generate_public(
    job_context: GenerationContext,
    locale: str,
) -> None:
    app = job_context.app
    locale_label = get_display_name(locale, app.localizer.locale)
    logging.getLogger(__name__).debug(
        app.localizer._("Generating localized public files in {locale}...").format(
            locale=locale_label,
        )
    )
    async for file_path in app.assets.copytree(
        Path("public") / "localized",
        app.project.configuration.localize_www_directory_path(locale),
    ):
        await app.renderer.render_file(
            file_path,
            job_context=job_context,
            localizer=await app.localizers.get(locale),
        )


async def _generate_static_public(
    app: App,
    job_context: Context,
) -> None:
    logging.getLogger(__name__).info(
        app.localizer._("Generating static public files...")
    )
    async for file_path in app.assets.copytree(
        Path("public") / "static", app.project.configuration.www_directory_path
    ):
        await app.renderer.render_file(
            file_path,
            job_context=job_context,
        )


async def _generate_entity_type_list_html(
    job_context: GenerationContext,
    locale: str,
    entity_type: type[Entity],
) -> None:
    app = job_context.app
    entity_type_name_fs = camel_case_to_kebab_case(get_entity_type_name(entity_type))
    entity_type_path = (
        app.project.configuration.localize_www_directory_path(locale)
        / entity_type_name_fs
    )
    template = app.jinja2_environment.select_template(
        [
            f"entity/page-list--{entity_type_name_fs}.html.j2",
            "entity/page-list.html.j2",
        ]
    )
    rendered_html = await template.render_async(
        job_context=job_context,
        localizer=await app.localizers.get(locale),
        page_resource=f"/{entity_type_name_fs}/index.html",
        entity_type=entity_type,
        entities=app.project.ancestry[entity_type],
    )
    async with await create_html_resource(entity_type_path) as f:
        await f.write(rendered_html)


async def _generate_entity_type_list_json(
    job_context: GenerationContext,
    entity_type: type[Entity & LinkedDataDumpable],
) -> None:
    app = job_context.app
    entity_type_name = get_entity_type_name(entity_type)
    entity_type_name_fs = camel_case_to_kebab_case(get_entity_type_name(entity_type))
    entity_type_path = (
        app.project.configuration.www_directory_path / entity_type_name_fs
    )
    data: DictDump[Dump] = {
        "$schema": app.static_url_generator.generate(
            f"schema.json#/definitions/response/{upper_camel_case_to_lower_camel_case(entity_type_name)}Collection",
            absolute=True,
        ),
        "collection": [],
    }
    for entity in app.project.ancestry[entity_type]:
        cast(list[str], data["collection"]).append(
            app.url_generator.generate(
                entity,
                "application/json",
                absolute=True,
            )
        )
    rendered_json = json.dumps(data)
    async with await create_json_resource(entity_type_path) as f:
        await f.write(rendered_json)


async def _generate_entity_html(
    job_context: GenerationContext,
    locale: str,
    entity_type: type[Entity],
    entity_id: str,
) -> None:
    app = job_context.app
    entity = app.project.ancestry[entity_type][entity_id]
    entity_type_name_fs = camel_case_to_kebab_case(get_entity_type_name(entity))
    entity_path = (
        app.project.configuration.localize_www_directory_path(locale)
        / entity_type_name_fs
        / entity.id
    )
    rendered_html = await app.jinja2_environment.select_template(
        [
            f"entity/page--{entity_type_name_fs}.html.j2",
            "entity/page.html.j2",
        ]
    ).render_async(
        job_context=job_context,
        localizer=await app.localizers.get(locale),
        page_resource=entity,
        entity_type=entity.type,
        entity=entity,
    )
    async with await create_html_resource(entity_path) as f:
        await f.write(rendered_html)


async def _generate_entity_json(
    job_context: GenerationContext,
    entity_type: type[Entity & LinkedDataDumpable],
    entity_id: str,
) -> None:
    app = job_context.app
    entity_type_name_fs = camel_case_to_kebab_case(get_entity_type_name(entity_type))
    entity_path = (
        app.project.configuration.www_directory_path / entity_type_name_fs / entity_id
    )
    entity = cast(
        "Entity & LinkedDataDumpable", app.project.ancestry[entity_type][entity_id]
    )
    rendered_json = json.dumps(await entity.dump_linked_data(app))
    async with await create_json_resource(entity_path) as f:
        await f.write(rendered_json)


async def _generate_sitemap(
    job_context: GenerationContext,
) -> None:
    app = job_context.app
    sitemap_template = app.jinja2_environment.get_template("sitemap.xml.j2")
    sitemaps = []
    sitemap: list[str] = []
    sitemap_length = 0
    sitemaps.append(sitemap)
    for locale in app.project.configuration.locales:
        for entity in app.project.ancestry:
            if isinstance(entity.id, GeneratedEntityId):
                continue
            if not isinstance(entity, UserFacingEntity):
                continue

            sitemap.append(
                app.url_generator.generate(
                    entity,
                    absolute=True,
                    locale=locale,
                    media_type="text/html",
                )
            )
            sitemap_length += 1

            if sitemap_length == 50_000:
                sitemap = []
                sitemap_length = 0
                sitemaps.append(sitemap)

    sitemaps_urls = []
    for index, sitemap in enumerate(sitemaps):
        sitemaps_urls.append(
            app.static_url_generator.generate(
                f"sitemap-{index}.xml",
                absolute=True,
            )
        )
        rendered_sitemap = await sitemap_template.render_async(
            {
                "urls": sitemap,
            }
        )
        async with aiofiles.open(
            app.project.configuration.www_directory_path / f"sitemap-{index}.xml", "w"
        ) as f:
            await f.write(rendered_sitemap)

    rendered_sitemap_index = await app.jinja2_environment.get_template(
        "sitemap-index.xml.j2"
    ).render_async(
        {
            "sitemaps_urls": sitemaps_urls,
        }
    )
    async with aiofiles.open(
        app.project.configuration.www_directory_path / "sitemap.xml", "w"
    ) as f:
        await f.write(rendered_sitemap_index)


async def _generate_json_schema(
    job_context: GenerationContext,
) -> None:
    app = job_context.app
    logging.getLogger(__name__).debug(app.localizer._("Generating JSON Schema..."))
    schema = Schema(app)
    rendered_json = json.dumps(await schema.build())
    async with await create_file(
        app.project.configuration.www_directory_path / "schema.json"
    ) as f:
        await f.write(rendered_json)


async def _generate_openapi(
    job_context: GenerationContext,
) -> None:
    app = job_context.app
    logging.getLogger(__name__).debug(
        app.localizer._("Generating OpenAPI specification...")
    )
    api_directory_path = app.project.configuration.www_directory_path / "api"
    rendered_json = json.dumps(await Specification(app).build())
    async with await create_json_resource(api_directory_path) as f:
        await f.write(rendered_json)


def _get_entity_type_jinja2_name(entity_type_name: str) -> str:
    return camel_case_to_snake_case(entity_type_name).replace(".", "__")
