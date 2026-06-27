"""
The map content plugin.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from betty.asset_directories.maps import maps
from betty.content_builder import ContentBuilderDefinition
from betty.content_builders.template import Template, TemplateBuild
from betty.entities.event import Event
from betty.entities.person import Person
from betty.entities.place import Place
from betty.extensions.webpack import Webpack
from betty.factory import Manufacturable
from betty.jinja_filters.webpack_entry_point_js import WebpackEntryPointJs
from betty.localizables.gettext import _
from betty.project import Project

if TYPE_CHECKING:
    from betty.document import Document


@final
@ContentBuilderDefinition(
    "map",
    label=_("Map"),
    requires={
        Project.asset_directories.require(maps),
        Project.extensions.require(Webpack),
        Project.jinja_filters.require(WebpackEntryPointJs),
    },
)
class Map(Template, Manufacturable):
    """
    An interactive map.

    .. plugin:: content-builder:map
    """

    @override
    @Project.require
    @classmethod
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
                and presence.event.privacy.publishable
                and presence.event.place
            )
        elif isinstance(document.resource, Place):
            places.append(document.resource)
        places = [place for place in places if place.privacy.publishable]
        if places:
            return "component/maps/map.html.j2", {
                "places": places,
            }
        return None
