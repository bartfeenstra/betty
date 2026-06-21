"""
The file referees content plugin.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from betty.asset_directories.raspberry_mint import raspberry_mint
from betty.content_builder import ContentBuilderDefinition
from betty.content_builders.template import Template, TemplateBuild
from betty.entities.file import File
from betty.factory import Manufacturable
from betty.localizables.gettext import _
from betty.project import Project

if TYPE_CHECKING:
    from betty.document import Document


@final
@ContentBuilderDefinition(
    "raspberry-mint-file-referees",
    label=_("File referees"),
    requires={Project.asset_directories.require(raspberry_mint)},
)
class FileReferees(Template, Manufacturable):
    """
    Show the entities referencing a document resource that is a file.

    .. plugin:: content-builder:raspberry-mint-file-referees
    """

    @override
    @Project.require
    @classmethod
    async def new(cls, project: Project, /) -> Self:
        return cls(jinja=await project.jinja)

    @override
    async def build_template(self, document: Document) -> TemplateBuild:
        if isinstance(document.resource, File):
            return "entity/list.html.j2", {
                "entities": [referee.referee for referee in document.resource.referees]
            }
        return None
