"""
The notes content plugin.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from betty.content_builder import ContentBuilderDefinition
from betty.content_builders.template import Template, TemplateBuild
from betty.entity.has_notes import HasNotes
from betty.factory import Manufacturable
from betty.locale.localizable.gettext import _
from betty.project import Project

if TYPE_CHECKING:
    from betty.document import Document


@final
@ContentBuilderDefinition("notes", label=_("Notes"))
class Notes(Template, Manufacturable):
    """
    .. plugin:: content-builder:notes.
    """

    @override
    @Project.require
    @classmethod
    async def new(cls, project: Project, /) -> Self:
        return cls(jinja=await project.jinja)

    @override
    async def build_template(self, document: Document) -> TemplateBuild:
        if isinstance(document.resource, HasNotes):
            return "component/notes.html.j2", {"notes": document.resource.notes}
        return None
