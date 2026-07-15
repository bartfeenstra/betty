"""
The place enclosures content plugin.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from betty.asset_directories.raspberry_mint import raspberry_mint
from betty.content_builder import ContentBuilderDefinition
from betty.content_builders.template import Template, TemplateBuild
from betty.entities.place import Place
from betty.factory import Manufacturable
from betty.localizables.gettext import _
from betty.project import Project

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.document import Document


@final
@ContentBuilderDefinition(
    "raspberry-mint-enclosures",
    label=_("Enclosures"),
    requires={Project.asset_directories.require(raspberry_mint)},
)
class Enclosures(Template, Manufacturable):
    """
    Show the places enclosed by a place document resource.

    .. plugin:: content-builder:raspberry-mint-enclosures
    """

    @override
    @Project.require
    @classmethod
    async def new(cls, project: Project, /) -> Self:
        return cls(jinja=await project.jinja)

    @override
    async def build_template(self, document: Document) -> TemplateBuild:
        if isinstance(document.resource, Place):
            return "component/raspberry-mint/enclosures.html.j2", {
                "enclosures": list(self._encloses(document.resource))
            }
        return None

    def _encloses(self, place: Place) -> Iterable[Place]:
        for enclosure in place.encloses:
            yield enclosure.encloses
            yield from self._encloses(enclosure.encloses)
