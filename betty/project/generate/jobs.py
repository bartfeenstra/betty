"""
Jobs.
"""

from __future__ import annotations

from asyncio import gather, to_thread
from io import BytesIO
from json import dumps
from math import ceil
from pathlib import Path
from typing import TYPE_CHECKING, cast, final, override

import aiofiles
from aiofiles.os import makedirs
from PIL import Image

from betty.entity import EntityDefinition, persistent_id
from betty.jinja import make_copy_function
from betty.job import Job
from betty.locale.localizable.gettext import _
from betty.locale.localize import DEFAULT_LOCALIZER
from betty.media_type.media_types import HTML, JSON
from betty.openapi import Specification
from betty.privacy import is_public
from betty.project.generate.file import (
    create_file,
    create_html_resource,
    create_json_resource,
)
from betty.project.schema import ProjectSchema
from betty.string import kebab_case_to_lower_camel_case

if TYPE_CHECKING:
    from collections.abc import MutableSequence

    from babel import Locale

    from betty.jinja import CopyFunction
    from betty.job.scheduler import Scheduler
    from betty.portable import PortableMapping
    from betty.project import Project


@final
class GenerateStaticPublicAssets(Job):
    """
    Generate a site's static public assets.
    """

    def __init__(self, *, project: Project):
        super().__init__(self.id_for(), priority=True)
        self._project = project

    @classmethod
    def id_for(cls) -> str:
        """
        Get the job ID.
        """
        return "generate-static-public-assets"

    @override
    async def do(self, scheduler: Scheduler, /) -> None:

        assets = await self._project.assets
        jinja = await self._project.jinja
        copy_function = make_copy_function(
            jinja,
            document=await self._project.new_document(context=scheduler.context),
            www_directory_path=self._project.www_directory,
            is_localized_and_multilingual=self._project.multilingual,
        )
        await gather(
            *[
                self._generate(scheduler, asset_path, copy_function)
                async for asset_path in assets.walk(Path("public") / "static")
            ]
        )

    async def _generate(
        self,
        scheduler: Scheduler,
        asset_path: Path,
        copy_function: CopyFunction,
    ) -> None:

        assets = await self._project.assets
        file_destination_path = self._project.www_directory / asset_path.relative_to(
            Path("public") / "static"
        )
        await makedirs(file_destination_path.parent, exist_ok=True)
        await copy_function(await assets.get(asset_path), file_destination_path)


@final
class GenerateSitemap(Job):
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

    def __init__(self, *, project: Project):
        super().__init__(self.id_for())
        self._project = project

    @classmethod
    def id_for(cls) -> str:
        """
        Get the job ID.
        """
        return "generate-sitemap"

    @override
    async def do(self, scheduler: Scheduler, /) -> None:
        context = scheduler.context

        url_generator = await self._project.url_generator

        await to_thread(
            self._project.www_directory.mkdir,
            exist_ok=True,
            parents=True,
        )

        sitemap_batches = []
        sitemap_batch_urls: MutableSequence[str] = []
        sitemap_batch_urls_length = 0
        sitemap_batches.append(sitemap_batch_urls)
        for locale in self._project.locales.keys():  # noqa: SIM118
            for entity in self._project.ancestry:
                if not persistent_id(entity):
                    continue
                if not entity.plugin().public_facing:
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
                self._project.www_directory / f"sitemap-{sitemap_batch_index}.xml",
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
        async with aiofiles.open(self._project.www_directory / "sitemap.xml", "w") as f:
            await f.write(rendered_sitemap)


@final
class GenerateRobotsTxt(Job):
    """
    Generate a site's robots.txt.
    """

    _ROBOTS_TXT_TEMPLATE = """Sitemap: {{{ sitemap }}}"""

    def __init__(self, *, project: Project):
        super().__init__(self.id_for())
        self._project = project

    @classmethod
    def id_for(cls) -> str:
        """
        Get the job ID.
        """
        return "generate-robots-txt"

    @override
    async def do(self, scheduler: Scheduler, /) -> None:

        url_generator = await self._project.url_generator
        rendered_robots_txt = self._ROBOTS_TXT_TEMPLATE.replace(
            "{{{ sitemap }}}",
            url_generator.generate("betty-static:///sitemap.xml", absolute=True),
        )
        await to_thread(
            self._project.www_directory.mkdir,
            exist_ok=True,
            parents=True,
        )
        async with aiofiles.open(
            self._project.www_directory / "robots.txt", mode="w"
        ) as f:
            await f.write(rendered_robots_txt)


@final
class GenerateOpenApi(Job):
    """
    Generate a site's OpenAPI specification.
    """

    def __init__(self, *, project: Project):
        super().__init__(self.id_for())
        self._project = project

    @classmethod
    def id_for(cls) -> str:
        """
        Get the job ID.
        """
        return "generate-openapi"

    @override
    async def do(self, scheduler: Scheduler, /) -> None:

        api_directory_path = self._project.www_directory / "api"
        rendered_json = dumps(await Specification(self._project).build())
        async with create_json_resource(api_directory_path) as f:
            await f.write(rendered_json)


@final
class GenerateLocalizedPublicAssets(Job):
    """
    Generate a site's localized public assets.
    """

    def __init__(self, *, project: Project):
        super().__init__(
            self.id_for(),
            dependencies={GenerateStaticPublicAssets.id_for()},
            priority=True,
        )
        self._project = project

    @classmethod
    def id_for(cls) -> str:
        """
        Get the job ID.
        """
        return "generate-localized-public-assets"

    @override
    async def do(self, scheduler: Scheduler, /) -> None:

        assets = await self._project.assets
        localizers = await self._project.localizers
        jinja = await self._project.jinja
        copy_functions = {
            locale: make_copy_function(
                jinja,
                document=await self._project.new_document(
                    context=scheduler.context,
                    localizer=localizers.get(locale),
                ),
                www_directory_path=self._project.www_directory,
                is_localized_and_multilingual=self._project.multilingual,
            )
            for locale in self._project.locales.keys()  # noqa: SIM118
        }
        await gather(
            *[
                self._generate(scheduler, asset_path, copy_functions[locale], locale)
                async for asset_path in assets.walk(Path("public") / "localized")
                for locale in self._project.locales.keys()  # noqa: SIM118
            ]
        )

    async def _generate(
        self,
        scheduler: Scheduler,
        asset_path: Path,
        copy_function: CopyFunction,
        locale: Locale,
    ) -> None:

        assets = await self._project.assets
        file_destination_path = self._project.localize_www_directory(
            locale
        ) / asset_path.relative_to(Path("public") / "localized")
        await makedirs(file_destination_path.parent, exist_ok=True)
        await copy_function(await assets.get(asset_path), file_destination_path)


@final
class GenerateJsonSchema(Job):
    """
    Generate the JSON schema for a site.
    """

    def __init__(self, *, project: Project):
        super().__init__(self.id_for())
        self._project = project

    @classmethod
    def id_for(cls) -> str:
        """
        Get the job ID.
        """
        return "generate-json-schema"

    @override
    async def do(self, scheduler: Scheduler, /) -> None:

        schema = await ProjectSchema.new(self._project)
        rendered_json = dumps(schema.schema)
        async with create_file(ProjectSchema.www_path(self._project)) as f:
            await f.write(rendered_json)


@final
class GenerateJsonErrorResponses(Job):
    """
    Generate JSON HTTP error responses.
    """

    def __init__(self, *, project: Project):
        super().__init__(self.id_for())
        self._project = project

    @classmethod
    def id_for(cls) -> str:
        """
        Get the job ID.
        """
        return "generate-json-error-responses"

    @override
    async def do(self, scheduler: Scheduler, /) -> None:

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
            for locale in self._project.locales.keys():  # noqa: SIM118
                async with create_file(
                    self._project.localize_www_directory(locale)
                    / ".error"
                    / f"{code}.json"
                ) as f:
                    await f.write(
                        dumps(
                            {
                                "$schema": await ProjectSchema.def_url(
                                    self._project, "errorResponse"
                                ),
                                "message": message.localize(DEFAULT_LOCALIZER),
                            }
                        )
                    )


@final
class GenerateFavicon(Job):
    """
    Generate a site's favicon.
    """

    def __init__(self, *, project: Project):
        super().__init__(self.id_for())
        self._project = project

    @classmethod
    def id_for(cls) -> str:
        """
        Get the job ID.
        """
        return "generate-favicon"

    @override
    async def do(self, scheduler: Scheduler, /) -> None:

        await to_thread(
            self._project.www_directory.mkdir,
            exist_ok=True,
            parents=True,
        )

        async with aiofiles.open(self._project.logo, "rb") as logo_f:
            logo = BytesIO(await logo_f.read())
        image = Image.open(logo)
        favicon = BytesIO()
        image.save(favicon, format="ICO")
        async with aiofiles.open(
            self._project.www_directory / "favicon.ico", "wb"
        ) as favicon_f:
            await favicon_f.write(favicon.getbuffer())


@final
class GenerateEntityTypesJson(Job):
    """
    Generate JSON resources for entity types.
    """

    def __init__(self, *, project: Project):
        super().__init__(self.id_for(), priority=True)
        self._project = project

    @classmethod
    def id_for(cls) -> str:
        """
        Get the job ID.
        """
        return "generate-entity-types-json"

    @override
    async def do(self, scheduler: Scheduler, /) -> None:
        await gather(
            *[
                scheduler.add(_GenerateEntityTypeJson(self._project, entity_type))
                async for entity_type in self._project.plugins[EntityDefinition]
            ]
        )


@final
class _GenerateEntityTypeJson(Job):
    def __init__(self, project: Project, entity_type: EntityDefinition):
        super().__init__(self.id_for(entity_type))
        self._project = project
        self._entity_type = entity_type

    @classmethod
    def id_for(cls, entity_type: EntityDefinition) -> str:
        return f"generate-entity-type-json:{entity_type.id}"

    @override
    async def do(self, scheduler: Scheduler, /) -> None:

        url_generator = await self._project.url_generator
        entity_type_path = self._project.www_directory / self._entity_type.id
        data: PortableMapping = {
            "$schema": await ProjectSchema.def_url(
                self._project,
                f"{kebab_case_to_lower_camel_case(self._entity_type.id)}EntityCollectionResponse",
            ),
            "collection": [],
        }
        for entity in self._project.ancestry[self._entity_type.cls]:
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
class GenerateEntityTypesHtml(Job):
    """
    Generate HTML pages for entity types.
    """

    def __init__(self, *, per_page: int = 50, project: Project):
        super().__init__(self.id_for(), priority=True)
        self._project = project
        self._per_page = per_page

    @classmethod
    def id_for(cls) -> str:
        """
        Get the job ID.
        """
        return "generate-entity-types-html"

    @override
    async def do(self, scheduler: Scheduler, /) -> None:

        await gather(
            *[
                scheduler.add(
                    _GenerateEntityTypeHtml(
                        self._project,
                        entity_type,
                        locale,
                        page,
                        self._per_page,
                        page_count,
                    )
                )
                async for entity_type in self._project.plugins[EntityDefinition]
                if entity_type.public_facing
                and (
                    entity_type.id in self._project.entity_types
                    and self._project.entity_types[entity_type.id].generate_html_list
                )
                and (
                    page_count := ceil(
                        len(self._project.ancestry[entity_type]) / self._per_page
                    )
                    # Always show at least the first page, even if there are no entities.
                    or 1
                )
                for page in range(page_count)
                for locale in self._project.locales.keys()  # noqa: SIM118
            ]
        )


@final
class _GenerateEntityTypeHtml(Job):
    def __init__(
        self,
        project: Project,
        entity_type: EntityDefinition,
        locale: Locale,
        page: int,
        per_page: int,
        page_count: int,
    ):
        super().__init__(self.id_for(entity_type, locale, page))
        self._project = project
        self._entity_type = entity_type
        self._locale = locale
        self._page = page
        self._per_page = per_page
        self._page_count = page_count

    @classmethod
    def id_for(cls, entity_type: EntityDefinition, locale: Locale, page: int) -> str:
        return f"generate-entity-type-html:{entity_type.id}:{locale}:{page}"

    @override
    async def do(self, scheduler: Scheduler, /) -> None:
        context = scheduler.context

        localizers = await self._project.localizers
        jinja = await self._project.jinja
        template = jinja.select_template(
            [
                f"entity/page-list--{self._entity_type.id}.html.j2",
                "entity/page-list.html.j2",
            ]
        )
        rendered_html = await template.render_async(
            document=await self._project.new_document(
                self._entity_type,
                self._entity_type,
                context=context,
                localizer=localizers.get(self._locale),
            ),
            page=self._page,
            per_page=self._per_page,
            page_count=self._page_count,
            page_entities=list(
                filter(is_public, self._project.ancestry[self._entity_type.cls])
            )[
                self._per_page * self._page : self._per_page * self._page
                + self._per_page
            ],
        )
        page_path = (
            self._project.localize_www_directory(self._locale) / self._entity_type.id
        )
        if self._page > 0:
            page_path /= f"page-{self._page + 1}"
        async with create_html_resource(page_path) as f:
            await f.write(rendered_html)


@final
class GenerateEntitiesJson(Job):
    """
    Generate JSON resources for entities.
    """

    def __init__(self, *, project: Project):
        super().__init__(self.id_for(), priority=True)
        self._project = project

    @classmethod
    def id_for(cls) -> str:
        """
        Get the job ID.
        """
        return "generate-entities-json"

    @override
    async def do(self, scheduler: Scheduler, /) -> None:

        await gather(
            *[
                scheduler.add(
                    _GenerateEntityJson(self._project, entity_type, entity.id)
                )
                async for entity_type in self._project.plugins[EntityDefinition]
                for entity in self._project.ancestry[entity_type.cls]
                if persistent_id(entity)
            ]
        )


@final
class _GenerateEntityJson(Job):
    def __init__(self, project: Project, entity_type: EntityDefinition, entity_id: str):
        super().__init__(self.id_for(entity_type, entity_id))
        self._project = project
        self._entity_type = entity_type
        self._entity_id = entity_id

    @classmethod
    def id_for(cls, entity_type: EntityDefinition, entity_id: str) -> str:
        return f"generate-entity-json:{entity_type.id}:{entity_id}"

    @override
    async def do(self, scheduler: Scheduler, /) -> None:

        entity = self._project.ancestry[self._entity_type.cls][self._entity_id]
        entity_path = (
            self._project.www_directory / self._entity_type.id / entity.public_id
        )
        rendered_json = dumps(await entity.dump_linked_data(self._project))
        async with create_json_resource(entity_path) as f:
            await f.write(rendered_json)


@final
class GenerateEntitiesHtml(Job):
    """
    Generate HTML pages for entities.
    """

    def __init__(self, *, project: Project):
        super().__init__(self.id_for(), priority=True)
        self._project = project

    @classmethod
    def id_for(cls) -> str:
        """
        Get the job ID.
        """
        return "generate-entities-html"

    @override
    async def do(self, scheduler: Scheduler, /) -> None:

        await gather(
            *[
                scheduler.add(
                    _GenerateEntityHtml(self._project, entity_type, entity.id, locale)
                )
                async for entity_type in self._project.plugins[EntityDefinition]
                if entity_type.public_facing
                for entity in self._project.ancestry[entity_type.cls]
                if persistent_id(entity) and is_public(entity)
                for locale in self._project.locales.keys()  # noqa: SIM118
            ]
        )


@final
class _GenerateEntityHtml(Job):
    def __init__(
        self,
        project: Project,
        entity_type: EntityDefinition,
        entity_id: str,
        locale: Locale,
    ):
        super().__init__(self.id_for(entity_type, entity_id, locale))
        self._project = project
        self._entity_type = entity_type
        self._entity_id = entity_id
        self._locale = locale

    @classmethod
    def id_for(
        cls, entity_type: EntityDefinition, entity_id: str, locale: Locale
    ) -> str:
        return f"generate-entity-html:{entity_type.id}:{entity_id}:{locale}"

    @override
    async def do(self, scheduler: Scheduler, /) -> None:
        context = scheduler.context

        localizers = await self._project.localizers
        jinja = await self._project.jinja
        entity = self._project.ancestry[self._entity_type.cls][self._entity_id]
        entity_path = (
            self._project.localize_www_directory(self._locale)
            / self._entity_type.id
            / entity.public_id
        )
        rendered_html = await jinja.select_template(
            [
                f"entity/page--{self._entity_type.id}.html.j2",
                "entity/page.html.j2",
            ]
        ).render_async(
            document=await self._project.new_document(
                entity,
                entity,
                context=context,
                localizer=localizers.get(self._locale),
            )
        )
        async with create_html_resource(entity_path) as f:
            await f.write(rendered_html)
