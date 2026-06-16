"""
Jobs.
"""

from __future__ import annotations

from asyncio import gather, to_thread
from io import BytesIO
from json import dumps
from math import ceil
from pathlib import Path
from typing import TYPE_CHECKING, Final, cast, final, override

from PIL import Image

from betty.entity import EntityDefinition
from betty.file import read, write
from betty.jinja import make_copy_function
from betty.job import Job
from betty.locale.localizable.gettext import _
from betty.locale.localize import default_localizer
from betty.media_types.html import HTML
from betty.media_types.json import JSON
from betty.openapi import Specification
from betty.project.schema import ProjectSchema
from betty.string import kebab_case_to_lower_camel_case

if TYPE_CHECKING:
    from collections.abc import MutableSequence

    from babel import Locale

    from betty.jinja import CopyFunction
    from betty.job.scheduler import Scheduler
    from betty.portable import PortableMapping
    from betty.project import Project


async def _create_resource(file: Path, content: str, /) -> None:
    await to_thread(file.parent.mkdir, exist_ok=True, parents=True)
    return await write(file, content)


async def _create_html_resource(resource: Path, content: str, /) -> None:
    await _create_resource(resource / "index.html", content)


async def _create_json_resource(resource: Path, content: str, /) -> None:
    await _create_resource(resource / "index.json", content)


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
        jinja = await self._project.jinja
        copy_function = make_copy_function(
            jinja,
            document=await self._project.new_document(context=scheduler.context),
            www_directory=self._project.www_directory,
            is_localized_and_multilingual=self._project.multilingual,
        )
        await gather(*[
            self._generate(asset_path, copy_function)
            async for asset_path in self._project.asset_directories.walk(
                Path("public") / "static"
            )
        ])

    async def _generate(self, asset: Path, copy_function: CopyFunction, /) -> None:
        file_destination_path = self._project.www_directory / asset.relative_to(
            Path("public") / "static"
        )
        await to_thread(file_destination_path.parent.mkdir, exist_ok=True, parents=True)
        await copy_function(
            await self._project.asset_directories.get(asset), file_destination_path
        )


@final
class GenerateSitemap(Job):
    """
    Generate a site's sitemap.
    """

    _sitemap_url_template: Final[str] = """<url>
        <loc>{{{ loc }}}</loc>
        <lastmod>{{{ lastmod }}}</lastmod>
    </url>
    """

    _sitemap_batch_template: Final[str] = """<?xml version="1.0" encoding="utf-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.sitemaps.org/schemas/sitemap/0.9 http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd">
        {{{ urls }}}
    </urlset>
    """

    _sitemap_sitemap_template: Final[str] = """<sitemap>
        <loc>{{{ loc }}}</loc>
    </sitemap>
    """

    _sitemap_template: Final[str] = """<?xml version="1.0" encoding="UTF-8"?>
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
                if not entity.id.persistent:
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
            rendered_sitemap_batch = self._sitemap_batch_template.replace(
                "{{{ urls }}}",
                "".join(
                    self._sitemap_url_template.replace(
                        "{{{ loc }}}", sitemap_batch_url
                    ).replace("{{{ lastmod }}}", context.start.isoformat())
                    for sitemap_batch_url in sitemap_batch_urls
                ),
            )
            await write(
                self._project.www_directory / f"sitemap-{sitemap_batch_index}.xml",
                rendered_sitemap_batch,
            )

        rendered_sitemap = self._sitemap_template.replace(
            "{{{ sitemaps }}}",
            "".join(
                self._sitemap_sitemap_template.replace("{{{ loc }}}", sitemap_url)
                for sitemap_url in sitemap_urls
            ),
        )
        await write(self._project.www_directory / "sitemap.xml", rendered_sitemap)


@final
class GenerateRobotsTxt(Job):
    """
    Generate a site's robots.txt.
    """

    _robots_txt_template: Final[str] = """Sitemap: {{{ sitemap }}}"""

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
        rendered_robots_txt = self._robots_txt_template.replace(
            "{{{ sitemap }}}",
            url_generator.generate("betty-static:///sitemap.xml", absolute=True),
        )
        await to_thread(self._project.www_directory.mkdir, exist_ok=True, parents=True)
        await write(self._project.www_directory / "robots.txt", rendered_robots_txt)


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
        await _create_json_resource(
            self._project.www_directory / "api",
            dumps(await Specification(self._project).build()),
        )


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
        localizers = await self._project.localizers
        jinja = await self._project.jinja
        copy_functions = {
            locale: make_copy_function(
                jinja,
                document=await self._project.new_document(
                    context=scheduler.context,
                    localizer=localizers.get(locale),
                ),
                www_directory=self._project.www_directory,
                is_localized_and_multilingual=self._project.multilingual,
            )
            for locale in self._project.locales.keys()  # noqa: SIM118
        }
        await gather(*[
            self._generate(asset, copy_functions[locale], locale)
            async for asset in self._project.asset_directories.walk(
                Path("public") / "localized"
            )
            for locale in self._project.locales.keys()  # noqa: SIM118
        ])

    async def _generate(
        self, asset: Path, copy_function: CopyFunction, locale: Locale
    ) -> None:
        file_destination = self._project.localize_www_directory(
            locale
        ) / asset.relative_to(Path("public") / "localized")
        await to_thread(file_destination.parent.mkdir, exist_ok=True, parents=True)
        await copy_function(
            await self._project.asset_directories.get(asset), file_destination
        )


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
        schema_file = ProjectSchema.www_path(self._project)
        await to_thread(schema_file.parent.mkdir, exist_ok=True, parents=True)
        await write(schema_file, rendered_json)


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
        codes = [
            (401, _("I'm sorry, dear, but it seems you're not logged in.")),
            (
                403,
                _(
                    "I'm sorry, dear, but it seems you're not allowed to view this page."
                ),
            ),
            (404, _("I'm sorry, dear, but it seems this page does not exist.")),
        ]
        for locale in self._project.locales.keys():  # noqa: SIM118
            directory = self._project.localize_www_directory(locale) / ".error"
            for code, message in codes:
                await to_thread(directory.mkdir, exist_ok=True, parents=True)
                await write(
                    directory / f"{code}.json",
                    dumps({
                        "$schema": await ProjectSchema.def_url(
                            self._project, "errorResponse"
                        ),
                        "message": message.localize(default_localizer),
                    }),
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
        await to_thread(self._project.www_directory.mkdir, exist_ok=True, parents=True)
        logo = BytesIO(await read(self._project.logo, mode="rb"))
        image = Image.open(logo)
        favicon = BytesIO()
        image.save(favicon, format="ICO")
        await write(
            self._project.www_directory / "favicon.ico", favicon.getvalue(), mode="wb"
        )


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
        await gather(*[
            scheduler.add(_GenerateEntityTypeJson(self._project, entity_type))
            async for entity_type in self._project.plugins[EntityDefinition]
        ])


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
        entity_type_directory = self._project.www_directory / self._entity_type.id
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
        await _create_json_resource(entity_type_directory, dumps(data))


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
        generate_entity_list_html = await self._project.generate_entity_list_html
        await gather(*[
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
            and (entity_type.id in generate_entity_list_html)
            and (
                page_count := ceil(
                    len(self._project.ancestry[entity_type]) / self._per_page
                )
                # Always show at least the first page, even if there are no entities.
                or 1
            )
            for page in range(page_count)
            for locale in self._project.locales.keys()  # noqa: SIM118
        ])


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
        template = jinja.select_template([
            f"entity/page-list--{self._entity_type.id}.html.j2",
            "entity/page-list.html.j2",
        ])
        rendered_html = await template.render_async(
            document=await self._project.new_document(
                self._entity_type,
                self._entity_type,
                context=context,
                localizer=localizers.get(self._locale),
                media_type=HTML,
            ),
            page=self._page,
            per_page=self._per_page,
            page_count=self._page_count,
            page_entities=[
                entity
                for entity in self._project.ancestry[self._entity_type.cls]
                if entity.public
            ][
                self._per_page * self._page : self._per_page * self._page
                + self._per_page
            ],
        )
        page_path = (
            self._project.localize_www_directory(self._locale) / self._entity_type.id
        )
        if self._page > 0:
            page_path /= f"page--{self._page + 1}"
        await _create_html_resource(page_path, rendered_html)


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
        await gather(*[
            scheduler.add(_GenerateEntityJson(self._project, entity_type, entity.id))
            async for entity_type in self._project.plugins[EntityDefinition]
            for entity in self._project.ancestry[entity_type.cls]
        ])


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
        entity_path = self._project.www_directory / self._entity_type.id / entity.id
        await _create_json_resource(
            entity_path, dumps(await entity.dump_linked_data(self._project))
        )


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
        await gather(*[
            scheduler.add(
                _GenerateEntityHtml(self._project, entity_type, entity.id, locale)
            )
            async for entity_type in self._project.plugins[EntityDefinition]
            if entity_type.public_facing
            for entity in self._project.ancestry[entity_type.cls]
            if entity.id.persistent and entity.public
            for locale in self._project.locales.keys()  # noqa: SIM118
        ])


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
            / entity.id
        )
        rendered_html = await jinja.select_template([
            f"entity/page--{self._entity_type.id}.html.j2",
            "entity/page.html.j2",
        ]).render_async(
            document=await self._project.new_document(
                entity,
                entity,
                context=context,
                localizer=localizers.get(self._locale),
                media_type=HTML,
            )
        )
        await _create_html_resource(entity_path, rendered_html)
