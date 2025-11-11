"""
Map content.
"""

from collections.abc import Mapping
from typing import Any, Self

from typing_extensions import override

from betty.config import DefaultConfigurable
from betty.content_provider import ContentProviderDefinition
from betty.content_provider.content_providers import Jinja2TemplateContentProvider
from betty.locale.localizable import _
from betty.model.config import EntityReferenceSequence
from betty.project import Project
from betty.resource import Context as ResourceContext


@ContentProviderDefinition(
    id="maps-map",
    label=_("Map"),
)
class Map(Jinja2TemplateContentProvider, DefaultConfigurable[EntityReferenceSequence]):
    """
    An interactive map.
    """

    _template = "maps/content-map.html.j2"

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
    async def _provide_data(self, resource: ResourceContext) -> Mapping[str, Any]:
        return {
            "entity": resource["resource"],
        }
