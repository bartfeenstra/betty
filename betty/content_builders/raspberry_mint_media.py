"""
The media content plugin.
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
    "raspberry-mint-media",
    label=_("Media"),
    description=_("A single file in a media display"),
    requires={Project.asset_directories.require(raspberry_mint)},
)
class Media(Template, Manufacturable):
    """
    A single file in a media display.

    .. plugin:: content-builder:raspberry-mint-media
    """

    @override
    @Project.require
    @classmethod
    async def new(cls, project: Project, /) -> Self:
        return cls(jinja=await project.jinja)

    @override
    async def build_template(self, document: Document) -> TemplateBuild:
        if isinstance(document.resource, File):
            return "component/raspberry-mint/media.html.j2", {
                "file": document.resource,
            }
        return None
