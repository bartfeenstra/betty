"""
The external links content plugin.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from betty.asset_directories.raspberry_mint import RASPBERRY_MINT
from betty.content import ContentBuilderDefinition
from betty.content_builders.template import Template, TemplateBuild
from betty.entity.has_links import HasLinks
from betty.factory import Manufacturable
from betty.locale.localizable.gettext import _
from betty.project import Project

if TYPE_CHECKING:
    from betty.document import Document


@final
@ContentBuilderDefinition(
    "raspberry-mint-external-links",
    label=_("External links"),
    requires={Project.asset_directories.require(RASPBERRY_MINT)},
)
class ExternalLinks(Template, Manufacturable):
    """
    External links.

    .. plugin:: content-builder:raspberry-mint-external-links
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
