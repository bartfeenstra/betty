"""
Map content.
"""

from typing import Self, override

from betty.ancestry.event import Event
from betty.ancestry.person import Person
from betty.ancestry.place import Place
from betty.content import ContentDefinition
from betty.content.contents import Template, TemplateBuild
from betty.document import Document
from betty.locale.localizable.gettext import _
from betty.project import Project
from betty.service.factory import Manufacturable
from betty.service.requirement.project import require_project


@ContentDefinition("maps-map", label=_("Map"))
class Map(Template, Manufacturable):
    """
    An interactive map.

    .. plugin:: content:maps-map
    """

    @override
    @classmethod
    @require_project
    async def new(cls, project: Project, /) -> Self:
        return cls(jinja=await project.jinja)

    @override
    async def build_template(self, document: Document) -> TemplateBuild:
        places = []
        if isinstance(document.resource, Event) and document.resource.place:
            places.append(document.resource.place)
        elif isinstance(document.resource, Person):
            places.extend(
                presence.event.place
                for presence in document.resource.presences
                if presence.public
                and presence.event.public
                and presence.event.place
                and presence.event.place.public
            )
        elif isinstance(document.resource, Place):
            places.append(
                document.resource,
            )
        if places:
            return "component/maps/map.html.j2", {
                "places": places,
            }
        return None


@ContentDefinition("maps-attribution", label=_("Map attribution"))
class Attribution(Template, Manufacturable):
    """
    The attribution for an interactive map.

    .. plugin:: content:maps-attribution
    """

    @override
    @classmethod
    @require_project
    async def new(cls, project: Project, /) -> Self:
        return cls(jinja=await project.jinja)

    @override
    async def build_template(self, document: Document) -> TemplateBuild:
        return "component/maps/attribution.html.j2"
