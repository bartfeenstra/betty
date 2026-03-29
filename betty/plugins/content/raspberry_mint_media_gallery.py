"""
The media gallery content plugin.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from betty.content import ContentDefinition
from betty.entity.has_file_references import HasFileReferences
from betty.locale.localizable.gettext import _
from betty.plugins.content.template import Template, TemplateBuild
from betty.plugins.extension._theme import associated_file_references
from betty.plugins.extension.raspberry_mint import RaspberryMint
from betty.project import Project
from betty.requirement import require
from betty.service.factory import Manufacturable

if TYPE_CHECKING:
    from betty.document import Document


@final
@ContentDefinition(
    "raspberry-mint-media-gallery",
    label=_("Media gallery"),
    description=_("Multiple files in a media gallery display"),
    requires={RaspberryMint},
)
class MediaGallery(Template, Manufacturable):
    """
    Multiple files in a media gallery display.

    .. plugin:: content:raspberry-mint-media-gallery
    """

    @override
    @classmethod
    @require(Project)
    async def new(cls, project: Project, /) -> Self:
        return cls(jinja=await project.jinja)

    @override
    async def build_template(self, document: Document) -> TemplateBuild:
        if isinstance(document.resource, HasFileReferences):
            return "component/raspberry-mint/media-gallery.html.j2", {
                "file_references": list(associated_file_references(document.resource))
            }
        return None
