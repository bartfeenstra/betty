"""
Dynamic content.
"""

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Self

from typing_extensions import override

from betty.config import DefaultConfigurable
from betty.content_provider import ContentProviderDefinition
from betty.content_provider.content_providers import Jinja2TemplateContentProvider
from betty.job import Context
from betty.locale.localizable import _
from betty.model.config import EntityReferenceSequence
from betty.project import Project

if TYPE_CHECKING:
    from collections.abc import MutableSequence

    from betty.model import Entity


@ContentProviderDefinition(
    id="raspberry-mint-featured-entities",
    label=_("Featured entities"),
)
class FeaturedEntities(
    Jinja2TemplateContentProvider, DefaultConfigurable[EntityReferenceSequence]
):
    """
    Featured entities.
    """

    _template = "component/featured-entities.html.j2"

    def __init__(self, project: Project, configuration: EntityReferenceSequence):
        super().__init__(project, configuration=configuration)

    @override
    @classmethod
    async def new_for_project(cls, project: Project) -> Self:
        return cls(project, configuration=cls.new_default_configuration())

    @override
    @classmethod
    def new_default_configuration(cls) -> EntityReferenceSequence:
        return EntityReferenceSequence()

    @override
    async def _provide_data(
        self, *, locale: str, job_context: Context | None, page_resource: Any
    ) -> Mapping[str, Any]:
        entities: MutableSequence[Entity] = []
        for entity in self.configuration:
            assert entity.entity_type is not None
            assert entity.entity_id is not None
            entities.append(
                self._project.ancestry[
                    self._project.app.entity_type_repository.get(entity.entity_type)
                ][entity.entity_id]
            )
        return {
            "entities": entities,
        }
