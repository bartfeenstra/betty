"""
The external links content plugin.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from betty.content import ContentDefinition
from betty.entity.has_links import HasLinks
from betty.factory import Manufacturable
from betty.locale.localizable.gettext import _
from betty.plugins.asset.raspberry_mint import RASPBERRY_MINT
from betty.plugins.content.template import Template, TemplateBuild
from betty.project import Project

if TYPE_CHECKING:
    from betty.document import Document


@final
@ContentDefinition(
    "raspberry-mint-external-links",
    label=_("External links"),
    requires={Project.assets.require(RASPBERRY_MINT)},
)
class ExternalLinks(Template, Manufacturable):
    """
    External links.

    .. plugin:: content:raspberry-mint-external-links
    """

    @override
    @Project.require
    @classmethod
    async def new(cls, project: Project, /) -> Self:
        return cls(jinja=await project.jinja)

    @override
    async def build_template(self, document: Document) -> TemplateBuild:
        if isinstance(document.resource, HasLinks):
            return "component/raspberry-mint/links.html.j2", {
                "links": document.resource.links
            }
        return None
