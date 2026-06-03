"""
The map attribution content plugin.
"""

from typing import Self, final, override

from betty.asset_directories.maps import MAPS
from betty.content import ContentBuilderDefinition
from betty.content_builders.template import Template, TemplateBuild
from betty.document import Document
from betty.factory import Manufacturable
from betty.locale.localizable.gettext import _
from betty.project import Project


@final
@ContentBuilderDefinition(
    "map-attribution",
    label=_("Map attribution"),
    requires={Project.asset_directories.require(MAPS)},
)
class MapAttribution(Template, Manufacturable):
    """
    The attribution for an interactive map.

    .. plugin:: content-builder:map-attribution
    """

    @override
    @Project.require
    @classmethod
    async def new(cls, project: Project, /) -> Self:
        return cls(jinja=await project.jinja)

    @override
    async def build_template(self, document: Document) -> TemplateBuild:
        return "component/maps/attribution.html.j2"
