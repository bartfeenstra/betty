"""
The citations content plugin.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from betty.content import ContentDefinition
from betty.entity.has_citations import HasCitations
from betty.factory import Manufacturable
from betty.locale.localizable.gettext import _
from betty.plugins.asset_directory.raspberry_mint import RASPBERRY_MINT
from betty.plugins.content.template import Template, TemplateBuild
from betty.project import Project

if TYPE_CHECKING:
    from betty.document import Document


@final
@ContentDefinition(
    "raspberry-mint-citations",
    label=_("Citations"),
    requires={Project.asset_directories.require(RASPBERRY_MINT)},
)
class Citations(Template, Manufacturable):
    """
    The citations for a document resource that is an entity.

    .. plugin:: content:raspberry-mint-citations
    """

    @override
    @Project.require
    @classmethod
    async def new(cls, project: Project, /) -> Self:
        return cls(jinja=await project.jinja)

    @override
    async def build_template(self, document: Document) -> TemplateBuild:
        if isinstance(document.resource, HasCitations):
            return "component/raspberry-mint/citations.html.j2", {
                "citations": document.resource.citations
            }
        return None
