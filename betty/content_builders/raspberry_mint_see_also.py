"""
The "see also" content plugin.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from betty.asset_directories.raspberry_mint import raspberry_mint
from betty.associations.has_links import HasLinks
from betty.content_builder import ContentBuilderDefinition
from betty.content_builders.template import Template, TemplateBuild
from betty.factory import Manufacturable
from betty.localizables.gettext import _
from betty.project import Project

if TYPE_CHECKING:
    from betty.document import Document


@final
@ContentBuilderDefinition(
    "raspberry-mint-see-also",
    label=_("See also"),
    requires={Project.asset_directories.require(raspberry_mint)},
)
class SeeAlso(Template, Manufacturable):
    """
    "See also" links.

    .. plugin:: content-builder:raspberry-mint-see-also
    """

    @override
    @Project.require
    @classmethod
    async def new(cls, project: Project, /) -> Self:
        return cls(jinja=await project.jinja)

    @override
    async def build_template(self, document: Document) -> TemplateBuild:
        if isinstance(document.resource, HasLinks):
            return "component/raspberry-mint/links.html.j2", {
                "links": document.resource.links
            }
        return None
