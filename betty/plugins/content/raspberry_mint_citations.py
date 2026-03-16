"""
The citations content plugin.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from betty.ancestry.has_citations import HasCitations
from betty.content import ContentDefinition
from betty.locale.localizable.gettext import _
from betty.plugins.content.template import Template, TemplateBuild
from betty.service.factory import Manufacturable
from betty.service.requirement.project import require_project

if TYPE_CHECKING:
    from betty.document import Document
    from betty.project import Project


@final
@ContentDefinition("raspberry-mint-citations", label=_("Citations"))
class Citations(Template, Manufacturable):
    """
    The citations for a document resource that is an entity.

    .. plugin:: content:raspberry-mint-citations
    """

    @override
    @classmethod
    @require_project
    async def new(cls, project: Project, /) -> Self:
        return cls(jinja=await project.jinja)

    @override
    async def build_template(self, document: Document) -> TemplateBuild:
        if isinstance(document.resource, HasCitations):
            return "component/raspberry-mint/citations.html.j2", {
                "citations": document.resource.citations
            }
        return None
