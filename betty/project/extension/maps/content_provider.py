"""
Map content.
"""

from collections.abc import Mapping
from typing import Any, Self

from typing_extensions import override

from betty.ancestry.event import Event
from betty.ancestry.person import Person
from betty.ancestry.place import Place
from betty.content_provider import ContentProviderDefinition
from betty.content_provider.content_providers import Template
from betty.document import Document
from betty.locale.localizable.gettext import _
from betty.project import Project
from betty.project.extension.maps import Maps
from betty.project.factory import require_project
from betty.requirement import HasRequirement, Requirement
from betty.service.level import ServiceLevel
from betty.service.level.factory import ServiceLevelDependentSelfFactory


@ContentProviderDefinition("maps-map", label=_("Map"))
class Map(Template, ServiceLevelDependentSelfFactory, HasRequirement):
    """
    An interactive map.
    """

    @override
    @classmethod
    @require_project
    async def new_for_services(cls, project: Project) -> Self:
        return cls(jinja2_environment=await project.jinja2_environment)

    @override
    async def _provide_data(self, document: Document) -> Mapping[str, Any]:
        places = []
        if isinstance(document.resource, Event):
            places = [document.resource.place] if document.resource.place else []
        elif isinstance(document.resource, Person):
            places = [
                presence.event.place
                for presence in document.resource.presences
                if presence.public
                and presence.event.public
                and presence.event.place
                and presence.event.place.public
            ]
        elif isinstance(document.resource, Place):
            places = [
                document.resource,
            ]
        return {
            "places": places,
        }

    @override
    @classmethod
    async def requirement(cls, services: ServiceLevel, /) -> Requirement | None:
        return await Maps.requirement_for(
            services, cls.plugin().reference_label_with_type
        )


@ContentProviderDefinition("maps-map-attribution", label=_("Map attribution"))
class MapAttribution(Template, ServiceLevelDependentSelfFactory, HasRequirement):
    """
    The attribution for an interactive map.
    """

    @override
    @classmethod
    @require_project
    async def new_for_services(cls, project: Project) -> Self:
        return cls(jinja2_environment=await project.jinja2_environment)

    @override
    @classmethod
    async def requirement(cls, services: ServiceLevel, /) -> Requirement | None:
        return await Maps.requirement_for(
            services, cls.plugin().reference_label_with_type
        )
