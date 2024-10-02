"""
Provide the Generation API.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import shutil
from asyncio import (
    create_task,
    Task,
    as_completed,
    Semaphore,
    CancelledError,
    sleep,
    to_thread,
)
from collections.abc import MutableSequence
from contextlib import suppress
from math import floor
from pathlib import Path
from typing import (
    cast,
    ParamSpec,
    Callable,
    Awaitable,
    Sequence,
    TYPE_CHECKING,
)

import aiofiles
from aiofiles.os import makedirs

from betty import model
from betty.asyncio import gather
from betty.locale import get_display_name
from betty.locale.localizable import _
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.model import UserFacingEntity, Entity, has_generated_entity_id
from betty.openapi import Specification
from betty.privacy import is_public
from betty.project import ProjectEvent, ProjectSchema, ProjectContext
from betty.project.generate.file import (
    create_file,
    create_html_resource,
    create_json_resource,
)
from betty.string import kebab_case_to_lower_camel_case

if TYPE_CHECKING:
    from betty.project import Project
    from betty.app import App
    from betty.serde.dump import DumpMapping, Dump
    from collections.abc import AsyncIterator


class GenerateSiteEvent(ProjectEvent):
    """
    Dispatched to generate (part of) a project's site.
    """

    pass


async def generate(project: Project) -> None:
    """
    Generate a new site.
    """
    logger = logging.getLogger(__name__)
    job_context = ProjectContext(project)
    app = project.app
    localizer = await app.localizer

    logger.info(
        localizer._("Generating your site to {output_directory}.").format(
            output_directory=project.configuration.output_directory_path
        )
    )
    with suppress(FileNotFoundError):
        await asyncio.to_thread(
            shutil.rmtree, project.configuration.output_directory_path
        )
    await makedirs(project.configuration.output_directory_path, exist_ok=True)

    # The static public assets may be overridden depending on the number of locales rendered, so ensure they are
    # generated before anything else.
    await _generate_static_public(job_context)

    jobs = [job async for job in _run_jobs(job_context)]
    log_job = create_task(_log_jobs_forever(app, jobs))
    for completed_job in as_completed(jobs):
        await completed_job
    log_job.cancel()
    await _log_jobs(app, jobs)

    project.configuration.output_directory_path.chmod(0o755)
    for directory_path_str, subdirectory_names, file_names in os.walk(
        project.configuration.output_directory_path
    ):
        directory_path = Path(directory_path_str)
        for subdirectory_name in subdirectory_names:
            (directory_path / subdirectory_name).chmod(0o755)
        for file_name in file_names:
            (directory_path / file_name).chmod(0o644)


async def _log_jobs(app: App, jobs: Sequence[Task[None]]) -> None:
    localizer = await app.localizer
    total_job_count = len(jobs)
    completed_job_count = len([job for job in jobs if job.done()])
    logging.getLogger(__name__).info(
        localizer._(
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


async def _run_jobs(job_context: ProjectContext) -> AsyncIterator[Task[None]]:
    project = job_context.project
    semaphore = Semaphore(512)
    yield _run_job(semaphore, _generate_dispatch, job_context)
    yield _run_job(semaphore, _generate_robots_txt, job_context)
    yield _run_job(semaphore, _generate_sitemap, job_context)
    yield _run_job(semaphore, _generate_json_schema, job_context)
    yield _run_job(semaphore, _generate_openapi, job_context)

    locales = list(project.configuration.locales.keys())

    for locale in locales:
        yield _run_job(semaphore, _generate_public, job_context, locale)

    async for entity_type in model.ENTITY_TYPE_REPOSITORY:
        if not issubclass(entity_type, UserFacingEntity):
            continue
        if (
            entity_type in project.configuration.entity_types
            and project.configuration.entity_types[entity_type].generate_html_list
        ):
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
        for entity in project.ancestry[entity_type]:
            if has_generated_entity_id(entity):
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


async def _generate_dispatch(job_context: ProjectContext) -> None:
    project = job_context.project
    await project.event_dispatcher.dispatch(GenerateSiteEvent(job_context))


async def _generate_public_asset(
    asset_path: Path, project: Project, job_context: ProjectContext, locale: str
) -> None:
    assets = await project.assets
    www_directory_path = project.configuration.localize_www_directory_path(locale)
    file_destination_path = www_directory_path / asset_path.relative_to(
        Path("public") / "localized"
    )
    await makedirs(file_destination_path.parent, exist_ok=True)
    await to_thread(shutil.copy2, await assets.get(asset_path), file_destination_path)
    renderer = await project.renderer
    await renderer.render_file(
        file_destination_path,
        job_context=job_context,
        localizer=await project.app.localizers.get(locale),
    )


async def _generate_public(
    job_context: ProjectContext,
    locale: str,
) -> None:
    project = job_context.project
    assets = await project.assets
    localizer = await project.app.localizer
    locale_label = get_display_name(locale, localizer.locale)
    logging.getLogger(__name__).debug(
        localizer._("Generating localized public files in {locale}...").format(
            locale=locale_label,
            localizer=await project.app.localizers.get(locale),
        )
    )
    await gather(
        *[
            _generate_public_asset(asset_path, project, job_context, locale)
            async for asset_path in assets.walk(Path("public") / "localized")
        ]
    )


async def _generate_static_public_asset(
    asset_path: Path, project: Project, job_context: ProjectContext
) -> None:
    assets = await project.assets
    file_destination_path = (
        project.configuration.www_directory_path
        / asset_path.relative_to(Path("public") / "static")
    )
    await makedirs(file_destination_path.parent, exist_ok=True)
    await to_thread(shutil.copy2, await assets.get(asset_path), file_destination_path)
    renderer = await project.renderer
    await renderer.render_file(file_destination_path, job_context=job_context)


async def _generate_static_public(
    job_context: ProjectContext,
) -> None:
    project = job_context.project
    app = project.app
    assets = await project.assets
    localizer = await app.localizer
    logging.getLogger(__name__).info(localizer._("Generating static public files..."))
    await gather(
        *[
            _generate_static_public_asset(asset_path, project, job_context)
            async for asset_path in assets.walk(Path("public") / "static")
        ],
        # Ensure favicon.ico exists, otherwise servers of Betty sites would log
        # many a 404 Not Found for it, because some clients eagerly try to see
        # if it exists.
        to_thread(
            shutil.copy2,
            await assets.get(Path("public") / "static" / "betty.ico"),
            project.configuration.www_directory_path / "favicon.ico",
        ),
        _generate_json_error_responses(project),
    )


async def _generate_json_error_responses(project: Project) -> None:
    for code, message in [
        (401, _("I'm sorry, dear, but it seems you're not logged in.")),
        (403, _("I'm sorry, dear, but it seems you're not allowed to view this page.")),
        (404, _("I'm sorry, dear, but it seems this page does not exist.")),
    ]:
        for locale in project.configuration.locales:
            async with create_file(
                project.configuration.localize_www_directory_path(locale)
                / ".error"
                / f"{code}.json"
            ) as f:
                await f.write(
                    json.dumps(
                        {
                            "$schema": ProjectSchema.def_url(project, "errorResponse"),
                            "message": message.localize(DEFAULT_LOCALIZER),
                        }
                    )
                )


async def _generate_entity_type_list_html(
    job_context: ProjectContext,
    locale: str,
    entity_type: type[Entity],
) -> None:
    project = job_context.project
    app = project.app
    jinja2_environment = await project.jinja2_environment
    entity_type_path = (
        project.configuration.localize_www_directory_path(locale)
        / entity_type.plugin_id()
    )
    template = jinja2_environment.select_template(
        [
            f"entity/page-list--{entity_type.plugin_id()}.html.j2",
            "entity/page-list.html.j2",
        ]
    )
    rendered_html = await template.render_async(
        job_context=job_context,
        localizer=await app.localizers.get(locale),
        page_resource=f"/{entity_type.plugin_id()}/index.html",
        entity_type=entity_type,
        entities=project.ancestry[entity_type],
    )
    async with create_html_resource(entity_type_path) as f:
        await f.write(rendered_html)


async def _generate_entity_type_list_json(
    job_context: ProjectContext,
    entity_type: type[Entity],
) -> None:
    project = job_context.project
    entity_type_path = (
        project.configuration.www_directory_path / entity_type.plugin_id()
    )
    data: DumpMapping[Dump] = {
        "$schema": ProjectSchema.def_url(
            project,
            f"{kebab_case_to_lower_camel_case(entity_type.plugin_id())}EntityCollectionResponse",
        ),
        "collection": [],
    }
    for entity in project.ancestry[entity_type]:
        cast(MutableSequence[str], data["collection"]).append(
            project.localized_url_generator.generate(
                entity,
                "application/json",
                absolute=True,
            )
        )
    rendered_json = json.dumps(data)
    async with create_json_resource(entity_type_path) as f:
        await f.write(rendered_json)


async def _generate_entity_html(
    job_context: ProjectContext,
    locale: str,
    entity_type: type[Entity],
    entity_id: str,
) -> None:
    project = job_context.project
    app = project.app
    jinja2_environment = await project.jinja2_environment
    entity = project.ancestry[entity_type][entity_id]
    entity_path = (
        project.configuration.localize_www_directory_path(locale)
        / entity_type.plugin_id()
        / entity.id
    )
    rendered_html = await jinja2_environment.select_template(
        [
            f"entity/page--{entity_type.plugin_id()}.html.j2",
            "entity/page.html.j2",
        ]
    ).render_async(
        job_context=job_context,
        localizer=await app.localizers.get(locale),
        page_resource=entity,
        entity_type=entity.type,
        entity=entity,
    )
    async with create_html_resource(entity_path) as f:
        await f.write(rendered_html)


async def _generate_entity_json(
    job_context: ProjectContext,
    entity_type: type[Entity],
    entity_id: str,
) -> None:
    project = job_context.project
    entity_path = (
        project.configuration.www_directory_path / entity_type.plugin_id() / entity_id
    )
    entity = project.ancestry[entity_type][entity_id]
    rendered_json = json.dumps(await entity.dump_linked_data(project))
    async with create_json_resource(entity_path) as f:
        await f.write(rendered_json)


_ROBOTS_TXT_TEMPLATE = """Sitemap: {{{ sitemap }}}"""


async def _generate_robots_txt(
    job_context: ProjectContext,
) -> None:
    rendered_robots_txt = _ROBOTS_TXT_TEMPLATE.replace(
        "{{{ sitemap }}}",
        job_context.project.static_url_generator.generate(
            "/sitemap.xml", absolute=True
        ),
    )
    await to_thread(
        job_context.project.configuration.www_directory_path.mkdir,
        exist_ok=True,
        parents=True,
    )
    async with aiofiles.open(
        job_context.project.configuration.www_directory_path / "robots.txt", mode="w"
    ) as f:
        await f.write(rendered_robots_txt)


_SITEMAP_URL_TEMPLATE = """<url>
    <loc>{{{ loc }}}</loc>
    <lastmod>{{{ lastmod }}}</lastmod>
</url>
"""


_SITEMAP_BATCH_TEMPLATE = """<?xml version="1.0" encoding="utf-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.sitemaps.org/schemas/sitemap/0.9 http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd">
    {{{ urls }}}
</urlset>
"""


_SITEMAP_SITEMAP_TEMPLATE = """<sitemap>
    <loc>{{{ loc }}}</loc>
</sitemap>
"""


_SITEMAP_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    {{{ sitemaps }}}
</sitemapindex>
"""


async def _generate_sitemap(
    job_context: ProjectContext,
) -> None:
    project = job_context.project
    sitemap_batches = []
    sitemap_batch_urls: MutableSequence[str] = []
    sitemap_batch_urls_length = 0
    sitemap_batches.append(sitemap_batch_urls)
    for locale in project.configuration.locales:
        for entity in project.ancestry:
            if has_generated_entity_id(entity):
                continue
            if not isinstance(entity, UserFacingEntity):
                continue

            sitemap_batch_urls.append(
                project.localized_url_generator.generate(
                    entity,
                    absolute=True,
                    locale=locale,
                    media_type="text/html",
                )
            )
            sitemap_batch_urls_length += 1

            if sitemap_batch_urls_length == 50_000:
                sitemap_batch_urls = []
                sitemap_batch_urls_length = 0
                sitemap_batches.append(sitemap_batch_urls)

    sitemap_urls = []
    for sitemap_batch_index, sitemap_batch_urls in enumerate(sitemap_batches):
        sitemap_urls.append(
            project.static_url_generator.generate(
                f"/sitemap-{sitemap_batch_index}.xml",
                absolute=True,
            )
        )
        rendered_sitemap_batch = _SITEMAP_BATCH_TEMPLATE.replace(
            "{{{ urls }}}",
            "".join(
                (
                    _SITEMAP_URL_TEMPLATE.replace(
                        "{{{ loc }}}", sitemap_batch_url
                    ).replace("{{{ lastmod }}}", job_context.start.isoformat())
                    for sitemap_batch_url in sitemap_batch_urls
                )
            ),
        )
        async with aiofiles.open(
            project.configuration.www_directory_path
            / f"sitemap-{sitemap_batch_index}.xml",
            "w",
        ) as f:
            await f.write(rendered_sitemap_batch)

    rendered_sitemap = _SITEMAP_TEMPLATE.replace(
        "{{{ sitemaps }}}",
        "".join(
            (
                _SITEMAP_SITEMAP_TEMPLATE.replace("{{{ loc }}}", sitemap_url)
                for sitemap_url in sitemap_urls
            )
        ),
    )
    async with aiofiles.open(
        project.configuration.www_directory_path / "sitemap.xml", "w"
    ) as f:
        await f.write(rendered_sitemap)


async def _generate_json_schema(
    job_context: ProjectContext,
) -> None:
    project = job_context.project
    localizer = await project.app.localizer
    logging.getLogger(__name__).debug(localizer._("Generating JSON Schema..."))
    schema = await ProjectSchema.new(project)
    rendered_json = json.dumps(schema.schema)
    async with create_file(ProjectSchema.www_path(project)) as f:
        await f.write(rendered_json)


async def _generate_openapi(
    job_context: ProjectContext,
) -> None:
    project = job_context.project
    app = project.app
    localizer = await app.localizer
    logging.getLogger(__name__).debug(
        localizer._("Generating OpenAPI specification...")
    )
    api_directory_path = project.configuration.www_directory_path / "api"
    rendered_json = json.dumps(await Specification(project).build())
    async with create_json_resource(api_directory_path) as f:
        await f.write(rendered_json)
