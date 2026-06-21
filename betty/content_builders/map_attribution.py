"""
The map attribution content plugin.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from betty.asset_directories.maps import maps
from betty.content_builder import ContentBuilderDefinition
from betty.content_builders.template import Template, TemplateBuild
from betty.factory import Manufacturable
from betty.localizables.gettext import _
from betty.project import Project

if TYPE_CHECKING:
    from betty.document import Document


@final
@ContentBuilderDefinition(
    "map-attribution",
    label=_("Map attribution"),
    requires={Project.asset_directories.require(maps)},
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
