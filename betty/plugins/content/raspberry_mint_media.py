"""
The media content plugin.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from betty.content import ContentDefinition
from betty.locale.localizable.gettext import _
from betty.plugins.content.template import Template, TemplateBuild
from betty.plugins.entity.file import File
from betty.service.factory import Manufacturable
from betty.service.requirement.project import require_project

if TYPE_CHECKING:
    from betty.document import Document
    from betty.project import Project


@final
@ContentDefinition(
    "raspberry-mint-media",
    label=_("Media"),
    description=_("A single file in a media display"),
)
class Media(Template, Manufacturable):
    """
    A single file in a media display.

    .. plugin:: content:raspberry-mint-media
    """

    @override
    @classmethod
    @require_project
    async def new(cls, project: Project, /) -> Self:
        return cls(jinja=await project.jinja)

    @override
    async def build_template(self, document: Document) -> TemplateBuild:
        if isinstance(document.resource, File):
            return "component/raspberry-mint/media.html.j2", {
                "file": document.resource,
            }
        return None
