"""
The map attribution content plugin.
"""

from typing import Self, final, override

from betty.content import ContentDefinition
from betty.document import Document
from betty.locale.localizable.gettext import _
from betty.plugins.asset.maps import Maps
from betty.plugins.content.template import Template, TemplateBuild
from betty.project import Project
from betty.requirement import require
from betty.service.factory import Manufacturable


@final
@ContentDefinition("map-attribution", label=_("Map attribution"), requires={Maps})
class MapAttribution(Template, Manufacturable):
    """
    The attribution for an interactive map.

    .. plugin:: content:map-attribution
    """

    @override
    @classmethod
    @require(Project)
    async def new(cls, project: Project, /) -> Self:
        return cls(jinja=await project.jinja)

    @override
    async def build_template(self, document: Document) -> TemplateBuild:
        return "component/maps/attribution.html.j2"
