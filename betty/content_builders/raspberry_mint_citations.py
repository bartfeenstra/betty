"""
The citations content plugin.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from betty.asset_directories.raspberry_mint import raspberry_mint
from betty.content_builder import ContentBuilderDefinition
from betty.content_builders.template import Template, TemplateBuild
from betty.entity.has_citations import HasCitations
from betty.factory import Manufacturable
from betty.localizables.gettext import _
from betty.project import Project

if TYPE_CHECKING:
    from betty.document import Document


@final
@ContentBuilderDefinition(
    "raspberry-mint-citations",
    label=_("Citations"),
    requires={Project.asset_directories.require(raspberry_mint)},
)
class Citations(Template, Manufacturable):
    """
    The citations for a document resource that is an entity.

    .. plugin:: content-builder:raspberry-mint-citations
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
