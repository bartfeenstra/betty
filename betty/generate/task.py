"""
Provide site generation tasks.
"""

from __future__ import annotations

import json
import logging
import shutil
from asyncio import (
    to_thread,
)
from collections.abc import MutableSequence
from pathlib import Path
from typing import cast, TYPE_CHECKING

import aiofiles
from aiofiles.os import makedirs

from betty import model
from betty.asyncio import gather
from betty.locale.localizable import _
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.project import ProjectSchema

if TYPE_CHECKING:
    from betty.project import Project
from betty.generate import GenerationContext, GenerateSiteEvent
from betty.generate.file import create_html_resource, create_json_resource, create_file
from betty.locale import get_display_name
from betty.model import UserFacingEntity, GeneratedEntityId, Entity
from betty.ancestry import is_public
from betty.openapi import Specification
from betty.string import kebab_case_to_lower_camel_case

if TYPE_CHECKING:
    from betty.generate.pool import _GenerationProcessPool
    from betty.serde.dump import DumpMapping, Dump
    from betty.project import Project


async def _generate_delegate(
    project: Project, process_pool: _GenerationProcessPool
) -> None:
    process_pool.delegate(_generate_dispatch)
    process_pool.delegate(_generate_sitemap)
    process_pool.delegate(_generate_json_schema)
    process_pool.delegate(_generate_openapi)

    locales = list(project.configuration.locales.keys())

    for locale in locales:
        process_pool.delegate(_generate_public, locale)

    async for entity_type in model.ENTITY_TYPE_REPOSITORY:
        if not issubclass(entity_type, UserFacingEntity):
            continue
        if (
            entity_type in project.configuration.entity_types
            and project.configuration.entity_types[entity_type].generate_html_list
        ):
            for locale in locales:
                process_pool.delegate(
                    _generate_entity_type_list_html,
                    locale,
                    entity_type,
                )
        process_pool.delegate(_generate_entity_type_list_json, entity_type)
        for entity in project.ancestry[entity_type]:
            if isinstance(entity.id, GeneratedEntityId):
                continue

            process_pool.delegate(_generate_entity_json, entity_type, entity.id)
            if is_public(entity):
                for locale in locales:
                    process_pool.delegate(
                        _generate_entity_html,
                        locale,
                        entity_type,
                        entity.id,
                    )


async def _generate_dispatch(job_context: GenerationContext) -> None:
    project = job_context.project
    await project.event_dispatcher.dispatch(GenerateSiteEvent(job_context))


async def _generate_public_asset(
    asset_path: Path, project: Project, job_context: GenerationContext, locale: str
) -> None:
    www_directory_path = project.configuration.localize_www_directory_path(locale)
    file_destination_path = www_directory_path / asset_path.relative_to(
        Path("public") / "localized"
    )
    await makedirs(file_destination_path.parent, exist_ok=True)
    await to_thread(
        shutil.copy2,
        project.assets[asset_path],
        file_destination_path,
    )
    await project.renderer.render_file(
        file_destination_path,
        job_context=job_context,
        localizer=await project.app.localizers.get(locale),
    )


async def _generate_public(
    job_context: GenerationContext,
    locale: str,
) -> None:
    project = job_context.project
    locale_label = get_display_name(locale, project.app.localizer.locale)
    logging.getLogger(__name__).debug(
        project.app.localizer._(
            "Generating localized public files in {locale}..."
        ).format(
            locale=locale_label,
            localizer=await project.app.localizers.get(locale),
        )
    )
    await gather(
        *(
            _generate_public_asset(asset_path, project, job_context, locale)
            for asset_path in project.assets.walk(Path("public") / "localized")
        )
    )


async def _generate_static_public_asset(
    asset_path: Path, project: Project, job_context: GenerationContext
) -> None:
    file_destination_path = (
        project.configuration.www_directory_path
        / asset_path.relative_to(Path("public") / "static")
    )
    await makedirs(file_destination_path.parent, exist_ok=True)
    await to_thread(
        shutil.copy2,
        project.assets[asset_path],
        file_destination_path,
    )
    await project.renderer.render_file(file_destination_path, job_context=job_context)


async def _generate_static_public(
    job_context: GenerationContext,
) -> None:
    project = job_context.project
    app = project.app
    logging.getLogger(__name__).info(
        app.localizer._("Generating static public files...")
    )
    await gather(
        *(
            _generate_static_public_asset(asset_path, project, job_context)
            for asset_path in project.assets.walk(Path("public") / "static")
        ),
        # Ensure favicon.ico exists, otherwise servers of Betty sites would log
        # many a 404 Not Found for it, because some clients eagerly try to see
        # if it exists.
        to_thread(
            shutil.copy2,
            project.assets[Path("public") / "static" / "betty.ico"],
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
            async with await create_file(
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
    job_context: GenerationContext,
    locale: str,
    entity_type: type[Entity],
) -> None:
    project = job_context.project
    app = project.app
    entity_type_path = (
        project.configuration.localize_www_directory_path(locale)
        / entity_type.plugin_id()
    )
    template = project.jinja2_environment.select_template(
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
    async with await create_html_resource(entity_type_path) as f:
        await f.write(rendered_html)


async def _generate_entity_type_list_json(
    job_context: GenerationContext,
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
            project.url_generator.generate(
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
    project = job_context.project
    app = project.app
    entity = project.ancestry[entity_type][entity_id]
    entity_path = (
        project.configuration.localize_www_directory_path(locale)
        / entity_type.plugin_id()
        / entity.id
    )
    rendered_html = await project.jinja2_environment.select_template(
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
    async with await create_html_resource(entity_path) as f:
        await f.write(rendered_html)


async def _generate_entity_json(
    job_context: GenerationContext,
    entity_type: type[Entity],
    entity_id: str,
) -> None:
    project = job_context.project
    entity_path = (
        project.configuration.www_directory_path / entity_type.plugin_id() / entity_id
    )
    entity = project.ancestry[entity_type][entity_id]
    rendered_json = json.dumps(await entity.dump_linked_data(project))
    async with await create_json_resource(entity_path) as f:
        await f.write(rendered_json)


async def _generate_sitemap(
    job_context: GenerationContext,
) -> None:
    project = job_context.project
    sitemap_template = project.jinja2_environment.get_template("sitemap.xml.j2")
    sitemaps = []
    sitemap: MutableSequence[str] = []
    sitemap_length = 0
    sitemaps.append(sitemap)
    for locale in project.configuration.locales:
        for entity in project.ancestry:
            if isinstance(entity.id, GeneratedEntityId):
                continue
            if not isinstance(entity, UserFacingEntity):
                continue

            sitemap.append(
                project.url_generator.generate(
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
            project.static_url_generator.generate(
                f"/sitemap-{index}.xml",
                absolute=True,
            )
        )
        rendered_sitemap = await sitemap_template.render_async(
            {
                "job_context": job_context,
                "urls": sitemap,
            }
        )
        async with aiofiles.open(
            project.configuration.www_directory_path / f"sitemap-{index}.xml", "w"
        ) as f:
            await f.write(rendered_sitemap)

    rendered_sitemap_index = await project.jinja2_environment.get_template(
        "sitemap-index.xml.j2"
    ).render_async(
        {
            "job_context": job_context,
            "sitemaps_urls": sitemaps_urls,
        }
    )
    async with aiofiles.open(
        project.configuration.www_directory_path / "sitemap.xml", "w"
    ) as f:
        await f.write(rendered_sitemap_index)


async def _generate_json_schema(
    job_context: GenerationContext,
) -> None:
    project = job_context.project
    logging.getLogger(__name__).debug(
        project.app.localizer._("Generating JSON Schema...")
    )
    schema = await ProjectSchema.new(project)
    rendered_json = json.dumps(schema.schema)
    async with await create_file(ProjectSchema.www_path(project)) as f:
        await f.write(rendered_json)


async def _generate_openapi(
    job_context: GenerationContext,
) -> None:
    project = job_context.project
    app = project.app
    logging.getLogger(__name__).debug(
        app.localizer._("Generating OpenAPI specification...")
    )
    api_directory_path = project.configuration.www_directory_path / "api"
    rendered_json = json.dumps(await Specification(project).build())
    async with await create_json_resource(api_directory_path) as f:
        await f.write(rendered_json)
