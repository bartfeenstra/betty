"""
The notes content plugin.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from betty.ancestry.has_notes import HasNotes
from betty.content import ContentDefinition
from betty.locale.localizable.gettext import _
from betty.plugins.content.template import Template, TemplateBuild
from betty.project import Project
from betty.requirement import require
from betty.service.factory import Manufacturable

if TYPE_CHECKING:
    from betty.document import Document


@final
@ContentDefinition("notes", label=_("Notes"))
class Notes(Template, Manufacturable):
    """
    .. plugin:: content:notes.
    """

    @override
    @classmethod
    @require(Project)
    async def new(cls, project: Project, /) -> Self:
        return cls(jinja=await project.jinja)

    @override
    async def build_template(self, document: Document) -> TemplateBuild:
        if isinstance(document.resource, HasNotes):
            return "component/notes.html.j2", {"notes": document.resource.notes}
        return None
