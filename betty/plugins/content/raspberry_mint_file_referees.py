"""
The file referees content plugin.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from betty.content import ContentDefinition
from betty.factory import Manufacturable
from betty.locale.localizable.gettext import _
from betty.plugins.asset_directory.raspberry_mint import RASPBERRY_MINT
from betty.plugins.content.template import Template, TemplateBuild
from betty.plugins.entity.file import File
from betty.project import Project

if TYPE_CHECKING:
    from betty.document import Document


@final
@ContentDefinition(
    "raspberry-mint-file-referees",
    label=_("File referees"),
    requires={Project.asset_directories.require(RASPBERRY_MINT)},
)
class FileReferees(Template, Manufacturable):
    """
    Show the entities referencing a document resource that is a file.

    .. plugin:: content:raspberry-mint-file-referees
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
