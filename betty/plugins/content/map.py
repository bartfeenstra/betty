"""
The map content plugin.
"""

from typing import Self, final, override

from betty.content import ContentDefinition
from betty.document import Document
from betty.entities.event import Event
from betty.entities.person import Person
from betty.entities.place import Place
from betty.factory import Manufacturable
from betty.locale.localizable.gettext import _
from betty.plugins.asset_directory.maps import MAPS
from betty.plugins.content.template import Template, TemplateBuild
from betty.plugins.extension.webpack import Webpack
from betty.plugins.jinja_filter.webpack_entry_point_js import WebpackEntryPointJs
from betty.project import Project


@final
@ContentDefinition(
    "map",
    label=_("Map"),
    requires={
        Project.asset_directories.require(MAPS),
        Project.extensions.require(Webpack),
        Project.jinja_filters.require(WebpackEntryPointJs),
    },
)
class Map(Template, Manufacturable):
    """
    An interactive map.

    .. plugin:: content:map
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
                if presence.public and presence.event.public and presence.event.place
            )
        elif isinstance(document.resource, Place):
            places.append(document.resource)
        places = [place for place in places if place.public]
        if places:
            return "component/maps/map.html.j2", {
                "places": places,
            }
        return None
