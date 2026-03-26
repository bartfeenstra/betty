"""
The media content plugin.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from betty.content import ContentDefinition
from betty.locale.localizable.gettext import _
from betty.plugins.asset.raspberry_mint import RaspberryMint
from betty.plugins.content.template import Template, TemplateBuild
from betty.plugins.entity.file import File
from betty.project import Project
from betty.requirement import require
from betty.service.factory import Manufacturable

if TYPE_CHECKING:
    from betty.document import Document


@final
@ContentDefinition(
    "raspberry-mint-media",
    label=_("Media"),
    description=_("A single file in a media display"),
    requires={RaspberryMint},
)
class Media(Template, Manufacturable):
    """
    A single file in a media display.

    .. plugin:: content:raspberry-mint-media
    """

    @override
    @classmethod
    @require(Project)
    async def new(cls, project: Project, /) -> Self:
        return cls(jinja=await project.jinja)

    @override
    async def build_template(self, document: Document) -> TemplateBuild:
        if isinstance(document.resource, File):
            return "component/raspberry-mint/media.html.j2", {
                "file": document.resource,
            }
        return None
