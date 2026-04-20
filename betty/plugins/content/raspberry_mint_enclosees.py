"""
The place enclosees content plugin.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from betty.content import ContentDefinition
from betty.factory import Manufacturable
from betty.locale.localizable.gettext import _
from betty.plugins.asset.raspberry_mint import RASPBERRY_MINT
from betty.plugins.content.template import Template, TemplateBuild
from betty.plugins.entity.place import Place
from betty.project import Project

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.document import Document


@final
@ContentDefinition(
    "raspberry-mint-enclosees",
    label=_("Enclosees"),
    requires={Project.assets.require(RASPBERRY_MINT)},
)
class Enclosees(Template, Manufacturable):
    """
    Show the places enclosed by a place document resource.

    .. plugin:: content:raspberry-mint-enclosees
    """

    @override
    @Project.require
    @classmethod
    async def new(cls, project: Project, /) -> Self:
        return cls(jinja=await project.jinja)

    @override
    async def build_template(self, document: Document) -> TemplateBuild:
        if isinstance(document.resource, Place):
            return "component/raspberry-mint/enclosees.html.j2", {
                "enclosees": list(self._enclosees(document.resource))
            }
        return None

    def _enclosees(self, place: Place) -> Iterable[Place]:
        for enclosure in place.enclosees:
            yield enclosure.enclosee
            yield from self._enclosees(enclosure.enclosee)
