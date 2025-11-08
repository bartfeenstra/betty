"""
Dynamic content.
"""

from typing import TYPE_CHECKING, Any, Self

from typing_extensions import override

from betty.config import DefaultConfigurable
from betty.content_provider import ContentProvider, ContentProviderDefinition
from betty.job import Context
from betty.locale.localizable import _
from betty.model.config import EntityReferenceSequence
from betty.plugin import ClassedPlugin
from betty.project import Project
from betty.project.factory import ProjectDependentFactory

if TYPE_CHECKING:
    from collections.abc import MutableSequence

    from betty.model import Entity


@ContentProviderDefinition(
    id="raspberry-mint-featured-entities",
    label=_("Featured entities"),
)
class FeaturedEntities(
    ContentProvider,
    ClassedPlugin,
    DefaultConfigurable[EntityReferenceSequence],
    ProjectDependentFactory,
):
    """
    Featured entities.
    """

    def __init__(self, project: Project, configuration: EntityReferenceSequence):
        super().__init__(configuration=configuration)
        self._project = project

    @override
    @classmethod
    async def new_for_project(cls, project: Project) -> Self:
        return cls(project, configuration=cls.new_default_configuration())

    @override
    @classmethod
    def new_default_configuration(cls) -> EntityReferenceSequence:
        return EntityReferenceSequence()

    @override
    async def provide(
        self, *, locale: str, page_resource: Any, job_context: Context | None = None
    ) -> str:
        localizers = await self._project.localizers
        jinja2_environment = await self._project.jinja2_environment
        entities: MutableSequence[Entity] = []
        for entity in self.configuration:
            assert entity.entity_type is not None
            assert entity.entity_id is not None
            entities.append(
                self._project.ancestry[
                    self._project.app.entity_type_repository.get(entity.entity_type)
                ][entity.entity_id]
            )
        return await jinja2_environment.get_template(
            "component/featured-entities.html.j2"
        ).render_async(
            job_context=job_context,
            localizer=localizers.get(locale),
            entities=entities,
        )
