"""
Jobs to generate HTML pages for entities.
"""

from __future__ import annotations

from asyncio import gather
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
            if entity.id.persistent and entity.publishable
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
        /,
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
