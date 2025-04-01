"""
Jobs.
"""

from __future__ import annotations

import shutil
from asyncio import gather, to_thread
from io import BytesIO
from json import dumps
from pathlib import Path
from typing import TYPE_CHECKING, cast, final

import aiofiles
from aiofiles.os import makedirs
from PIL import Image
from typing_extensions import override

from betty import model
from betty.job import Job
from betty.locale.localizable import _
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.media_type.media_types import HTML, JSON
from betty.model import Entity, persistent_id
from betty.openapi import Specification
from betty.privacy import is_public
from betty.project import ProjectContext, ProjectSchema
from betty.project.generate.file import (
    create_file,
    create_html_resource,
    create_json_resource,
)
from betty.string import kebab_case_to_lower_camel_case
from betty.user import UserFacing

if TYPE_CHECKING:
    from collections.abc import MutableSequence

    from betty.job.scheduler import Scheduler
    from betty.serde.dump import Dump, DumpMapping


@final
class GenerateStaticPublicAssets(Job[ProjectContext]):
    """
    Generate a site's static public assets.
    """

    def __init__(self):
        super().__init__(self.id_for(), priority=True)

    @classmethod
    def id_for(cls) -> str:
        """
        Get the job ID.
        """
        return "generate-static-public-assets"

    @override
    async def do(self, scheduler: Scheduler[ProjectContext], /) -> None:
        project = scheduler.context.project
        app = project.app
        assets = await project.assets
        await app.localizer
        await gather(
            *[
                self._generate(scheduler, asset_path)
                async for asset_path in assets.walk(Path("public") / "static")
            ]
        )

    async def _generate(
        self, scheduler: Scheduler[ProjectContext], asset_path: Path, /
    ) -> None:
        context = scheduler.context
        project = context.project
        assets = await project.assets
        file_destination_path = (
            project.configuration.www_directory_path
            / asset_path.relative_to(Path("public") / "static")
        )
        await makedirs(file_destination_path.parent, exist_ok=True)
        await to_thread(
            shutil.copy2, await assets.get(asset_path), file_destination_path
        )
        renderer = await project.renderer
        await renderer.render_file(file_destination_path, job_context=context)


@final
class GenerateSitemap(Job[ProjectContext]):
    """
    Generate a site's sitemap.
    """

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

    def __init__(self):
        super().__init__(self.id_for())

    @classmethod
    def id_for(cls) -> str:
        """
        Get the job ID.
        """
        return "generate-sitemap"

    @override
    async def do(self, scheduler: Scheduler[ProjectContext], /) -> None:
        context = scheduler.context
        project = context.project
        url_generator = await project.url_generator

        await to_thread(
            project.configuration.www_directory_path.mkdir,
            exist_ok=True,
            parents=True,
        )

        sitemap_batches = []
        sitemap_batch_urls: MutableSequence[str] = []
        sitemap_batch_urls_length = 0
        sitemap_batches.append(sitemap_batch_urls)
        for locale in project.configuration.locales:
            for entity in project.ancestry:
                if not persistent_id(entity):
                    continue
                if not isinstance(entity, UserFacing):
                    continue

                sitemap_batch_urls.append(
                    url_generator.generate(
                        entity,
                        absolute=True,
                        locale=locale,
                        media_type=HTML,
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
                url_generator.generate(
                    f"betty-static:///sitemap-{sitemap_batch_index}.xml",
                    absolute=True,
                )
            )
            rendered_sitemap_batch = self._SITEMAP_BATCH_TEMPLATE.replace(
                "{{{ urls }}}",
                "".join(
                    self._SITEMAP_URL_TEMPLATE.replace(
                        "{{{ loc }}}", sitemap_batch_url
                    ).replace("{{{ lastmod }}}", context.start.isoformat())
                    for sitemap_batch_url in sitemap_batch_urls
                ),
            )
            async with aiofiles.open(
                project.configuration.www_directory_path
                / f"sitemap-{sitemap_batch_index}.xml",
                "w",
            ) as f:
                await f.write(rendered_sitemap_batch)

        rendered_sitemap = self._SITEMAP_TEMPLATE.replace(
            "{{{ sitemaps }}}",
            "".join(
                self._SITEMAP_SITEMAP_TEMPLATE.replace("{{{ loc }}}", sitemap_url)
                for sitemap_url in sitemap_urls
            ),
        )
        async with aiofiles.open(
            project.configuration.www_directory_path / "sitemap.xml", "w"
        ) as f:
            await f.write(rendered_sitemap)


@final
class GenerateRobotsTxt(Job[ProjectContext]):
    """
    Generate a site's robots.txt.
    """

    _ROBOTS_TXT_TEMPLATE = """Sitemap: {{{ sitemap }}}"""

    def __init__(self):
        super().__init__(self.id_for())

    @classmethod
    def id_for(cls) -> str:
        """
        Get the job ID.
        """
        return "generate-robots-txt"

    @override
    async def do(self, scheduler: Scheduler[ProjectContext], /) -> None:
        project = scheduler.context.project
        url_generator = await project.url_generator
        rendered_robots_txt = self._ROBOTS_TXT_TEMPLATE.replace(
            "{{{ sitemap }}}",
            url_generator.generate("betty-static:///sitemap.xml", absolute=True),
        )
        await to_thread(
            project.configuration.www_directory_path.mkdir,
            exist_ok=True,
            parents=True,
        )
        async with aiofiles.open(
            project.configuration.www_directory_path / "robots.txt", mode="w"
        ) as f:
            await f.write(rendered_robots_txt)


@final
class GenerateOpenApi(Job[ProjectContext]):
    """
    Generate a site's OpenAPI specification.
    """

    def __init__(self):
        super().__init__(self.id_for())

    @classmethod
    def id_for(cls) -> str:
        """
        Get the job ID.
        """
        return "generate-openapi"

    @override
    async def do(self, scheduler: Scheduler[ProjectContext], /) -> None:
        project = scheduler.context.project
        api_directory_path = project.configuration.www_directory_path / "api"
        rendered_json = dumps(await Specification(project).build())
        async with create_json_resource(api_directory_path) as f:
            await f.write(rendered_json)


@final
class GenerateLocalizedPublicAssets(Job[ProjectContext]):
    """
    Generate a site's localized public assets.
    """

    def __init__(self):
        super().__init__(
            self.id_for(),
            dependencies={GenerateStaticPublicAssets.id_for()},
            priority=True,
        )

    @classmethod
    def id_for(cls) -> str:
        """
        Get the job ID.
        """
        return "generate-localized-public-assets"

    @override
    async def do(self, scheduler: Scheduler[ProjectContext], /) -> None:
        context = scheduler.context
        project = context.project
        assets = await project.assets
        async for asset_path in assets.walk(Path("public") / "localized"):
            await self._generate_localized_public_asset(context, asset_path)

    async def _generate_localized_public_asset(
        self, context: ProjectContext, asset_path: Path
    ) -> None:
        await gather(
            *[
                self._generate_localized_public_asset_for_locale(
                    context, asset_path=asset_path, locale=locale
                )
                for locale in context.project.configuration.locales
            ]
        )

    async def _generate_localized_public_asset_for_locale(
        self, context: ProjectContext, *, asset_path: Path, locale: str
    ) -> None:
        project = context.project
        assets = await project.assets
        localizers = await project.localizers
        www_directory_path = project.configuration.localize_www_directory_path(locale)
        file_destination_path = www_directory_path / asset_path.relative_to(
            Path("public") / "localized"
        )
        await makedirs(file_destination_path.parent, exist_ok=True)
        await to_thread(
            shutil.copy2, await assets.get(asset_path), file_destination_path
        )
        renderer = await project.renderer
        await renderer.render_file(
            file_destination_path, job_context=context, localizer=localizers.get(locale)
        )


@final
class GenerateJsonSchema(Job[ProjectContext]):
    """
    Generate the JSON schema for a site.
    """

    def __init__(self):
        super().__init__(self.id_for())

    @classmethod
    def id_for(cls) -> str:
        """
        Get the job ID.
        """
        return "generate-json-schema"

    @override
    async def do(self, scheduler: Scheduler[ProjectContext], /) -> None:
        project = scheduler.context.project
        schema = await ProjectSchema.new_for_project(project)
        rendered_json = dumps(schema.schema)
        async with create_file(ProjectSchema.www_path(project)) as f:
            await f.write(rendered_json)


@final
class GenerateJsonErrorResponses(Job[ProjectContext]):
    """
    Generate JSON HTTP error responses.
    """

    def __init__(self):
        super().__init__(self.id_for())

    @classmethod
    def id_for(cls) -> str:
        """
        Get the job ID.
        """
        return "generate-json-error-responses"

    @override
    async def do(self, scheduler: Scheduler[ProjectContext], /) -> None:
        project = scheduler.context.project
        for code, message in [
            (401, _("I'm sorry, dear, but it seems you're not logged in.")),
            (
                403,
                _(
                    "I'm sorry, dear, but it seems you're not allowed to view this page."
                ),
            ),
            (404, _("I'm sorry, dear, but it seems this page does not exist.")),
        ]:
            for locale in project.configuration.locales:
                async with create_file(
                    project.configuration.localize_www_directory_path(locale)
                    / ".error"
                    / f"{code}.json"
                ) as f:
                    await f.write(
                        dumps(
                            {
                                "$schema": await ProjectSchema.def_url(
                                    project, "errorResponse"
                                ),
                                "message": message.localize(DEFAULT_LOCALIZER),
                            }
                        )
                    )


@final
class GenerateFavicon(Job[ProjectContext]):
    """
    Generate a site's favicon.
    """

    def __init__(self):
        super().__init__(self.id_for())

    @classmethod
    def id_for(cls) -> str:
        """
        Get the job ID.
        """
        return "generate-favicon"

    @override
    async def do(self, scheduler: Scheduler[ProjectContext], /) -> None:
        project = scheduler.context.project

        await to_thread(
            project.configuration.www_directory_path.mkdir,
            exist_ok=True,
            parents=True,
        )

        async with aiofiles.open(project.logo, "rb") as logo_f:
            logo = BytesIO(await logo_f.read())
        image = Image.open(logo)
        favicon = BytesIO()
        image.save(favicon, format="ICO")
        async with aiofiles.open(
            project.configuration.www_directory_path / "favicon.ico", "wb"
        ) as favicon_f:
            await favicon_f.write(favicon.getbuffer())


@final
class GenerateEntityTypesJson(Job[ProjectContext]):
    """
    Generate JSON resources for entity types.
    """

    def __init__(self):
        super().__init__(self.id_for(), priority=True)

    @classmethod
    def id_for(cls) -> str:
        """
        Get the job ID.
        """
        return "generate-entity-types-json"

    @override
    async def do(self, scheduler: Scheduler[ProjectContext], /) -> None:
        await gather(
            *[
                scheduler.add(_GenerateEntityTypeJson(entity_type))
                async for entity_type in model.ENTITY_TYPE_REPOSITORY
            ]
        )


@final
class _GenerateEntityTypeJson(Job[ProjectContext]):
    def __init__(self, entity_type: type[Entity]):
        super().__init__(self.id_for(entity_type))
        self._entity_type = entity_type

    @classmethod
    def id_for(cls, entity_type: type[Entity]) -> str:
        return f"generate-entity-type-json:{entity_type.plugin_id()}"

    @override
    async def do(self, scheduler: Scheduler[ProjectContext], /) -> None:
        project = scheduler.context.project
        url_generator = await project.url_generator
        entity_type_path = (
            project.configuration.www_directory_path / self._entity_type.plugin_id()
        )
        data: DumpMapping[Dump] = {
            "$schema": await ProjectSchema.def_url(
                project,
                f"{kebab_case_to_lower_camel_case(self._entity_type.plugin_id())}EntityCollectionResponse",
            ),
            "collection": [],
        }
        for entity in project.ancestry[self._entity_type]:
            cast("MutableSequence[str]", data["collection"]).append(
                url_generator.generate(
                    entity,
                    media_type=JSON,
                    absolute=True,
                )
            )
        rendered_json = dumps(data)
        async with create_json_resource(entity_type_path) as f:
            await f.write(rendered_json)


@final
class GenerateEntityTypesHtml(Job[ProjectContext]):
    """
    Generate HTML pages for entity types.
    """

    def __init__(self):
        super().__init__(self.id_for(), priority=True)

    @classmethod
    def id_for(cls) -> str:
        """
        Get the job ID.
        """
        return "generate-entity-types-html"

    @override
    async def do(self, scheduler: Scheduler[ProjectContext], /) -> None:
        project = scheduler.context.project
        await gather(
            *[
                scheduler.add(_GenerateEntityTypeHtml(entity_type, locale))
                async for entity_type in model.ENTITY_TYPE_REPOSITORY
                for locale in project.configuration.locales
                if issubclass(entity_type, UserFacing)
                and (
                    entity_type in project.configuration.entity_types
                    and project.configuration.entity_types[
                        entity_type
                    ].generate_html_list
                )
            ]
        )


@final
class _GenerateEntityTypeHtml(Job[ProjectContext]):
    def __init__(self, entity_type: type[Entity & UserFacing], locale: str):
        super().__init__(self.id_for(entity_type, locale))
        self._entity_type = entity_type
        self._locale = locale

    @classmethod
    def id_for(cls, entity_type: type[Entity & UserFacing], locale: str) -> str:
        return f"generate-entity-type-hml:{entity_type.plugin_id()}:{locale}"

    @override
    async def do(self, scheduler: Scheduler[ProjectContext], /) -> None:
        context = scheduler.context
        project = context.project
        localizers = await project.localizers
        jinja2_environment = await project.jinja2_environment
        entity_type_path = (
            project.configuration.localize_www_directory_path(self._locale)
            / self._entity_type.plugin_id()
        )
        template = jinja2_environment.select_template(
            [
                f"entity/page-list--{self._entity_type.plugin_id()}.html.j2",
                "entity/page-list.html.j2",
            ]
        )
        rendered_html = await template.render_async(
            job_context=context,
            localizer=localizers.get(self._locale),
            page_resource=self._entity_type,
            entity_type=self._entity_type,
            entities=project.ancestry[self._entity_type],
        )
        async with create_html_resource(entity_type_path) as f:
            await f.write(rendered_html)


@final
class GenerateEntitiesJson(Job[ProjectContext]):
    """
    Generate JSON resources for entities.
    """

    def __init__(self):
        super().__init__(self.id_for(), priority=True)

    @classmethod
    def id_for(cls) -> str:
        """
        Get the job ID.
        """
        return "generate-entities-json"

    @override
    async def do(self, scheduler: Scheduler[ProjectContext], /) -> None:
        await gather(
            *[
                scheduler.add(_GenerateEntityJson(entity_type, entity.id))
                async for entity_type in model.ENTITY_TYPE_REPOSITORY
                for entity in scheduler.context.project.ancestry[entity_type]
                if persistent_id(entity)
            ]
        )


@final
class _GenerateEntityJson(Job[ProjectContext]):
    def __init__(self, entity_type: type[Entity], entity_id: str):
        super().__init__(self.id_for(entity_type, entity_id))
        self._entity_type = entity_type
        self._entity_id = entity_id

    @classmethod
    def id_for(cls, entity_type: type[Entity], entity_id: str) -> str:
        return f"generate-entity-json:{entity_type.plugin_id()}:{entity_id}"

    @override
    async def do(self, scheduler: Scheduler[ProjectContext], /) -> None:
        project = scheduler.context.project
        entity_path = (
            project.configuration.www_directory_path
            / self._entity_type.plugin_id()
            / self._entity_id
        )
        entity = project.ancestry[self._entity_type][self._entity_id]
        rendered_json = dumps(await entity.dump_linked_data(project))
        async with create_json_resource(entity_path) as f:
            await f.write(rendered_json)


@final
class GenerateEntitiesHtml(Job[ProjectContext]):
    """
    Generate HTML pages for entities.
    """

    def __init__(self):
        super().__init__(self.id_for(), priority=True)

    @classmethod
    def id_for(cls) -> str:
        """
        Get the job ID.
        """
        return "generate-entities-html"

    @override
    async def do(self, scheduler: Scheduler[ProjectContext], /) -> None:
        project = scheduler.context.project
        locales = list(project.configuration.locales)
        await gather(
            *[
                scheduler.add(_GenerateEntityHtml(entity_type, entity.id, locale))
                async for entity_type in model.ENTITY_TYPE_REPOSITORY
                if issubclass(entity_type, UserFacing)
                for entity in project.ancestry[entity_type]
                if persistent_id(entity) and is_public(entity)
                for locale in locales
            ]
        )


@final
class _GenerateEntityHtml(Job[ProjectContext]):
    def __init__(
        self, entity_type: type[Entity & UserFacing], entity_id: str, locale: str
    ):
        super().__init__(self.id_for(entity_type, entity_id, locale))
        self._entity_type = entity_type
        self._entity_id = entity_id
        self._locale = locale

    @classmethod
    def id_for(
        cls, entity_type: type[Entity & UserFacing], entity_id: str, locale: str
    ) -> str:
        return f"generate-entity-html:{entity_type.plugin_id()}:{entity_id}:{locale}"

    @override
    async def do(self, scheduler: Scheduler[ProjectContext], /) -> None:
        context = scheduler.context
        project = context.project
        localizers = await project.localizers
        jinja2_environment = await project.jinja2_environment
        entity = project.ancestry[self._entity_type][self._entity_id]
        entity_path = (
            project.configuration.localize_www_directory_path(self._locale)
            / self._entity_type.plugin_id()
            / entity.id
        )
        rendered_html = await jinja2_environment.select_template(
            [
                f"entity/page--{self._entity_type.plugin_id()}.html.j2",
                "entity/page.html.j2",
            ]
        ).render_async(
            job_context=context,
            localizer=localizers.get(self._locale),
            page_resource=entity,
            entity_type=type(entity),
            entity=entity,
        )
        async with create_html_resource(entity_path) as f:
            await f.write(rendered_html)
