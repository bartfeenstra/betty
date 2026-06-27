"""
Jobs to generate HTML pages for entity types.
"""

from __future__ import annotations

from asyncio import gather
from math import ceil
from typing import TYPE_CHECKING, final, override

from betty.entity import EntityDefinition
from betty.job import Job
from betty.jobs import _create_html_resource
from betty.media_types.html import HTML

if TYPE_CHECKING:
    from babel import Locale

    from betty.job.scheduler import Scheduler
    from betty.project import Project


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
                if entity.privacy.publishable
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
