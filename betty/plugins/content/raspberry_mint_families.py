"""
The families content plugin.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from betty.asset_directories.raspberry_mint import RASPBERRY_MINT
from betty.content import ContentDefinition
from betty.entities.person import Person
from betty.factory import Manufacturable
from betty.locale.localizable.gettext import _
from betty.plugins.content.template import Template, TemplateBuild
from betty.plugins.extension._theme import person_descendant_families
from betty.project import Project

if TYPE_CHECKING:
    from betty.document import Document


@final
@ContentDefinition(
    "raspberry-mint-families",
    label=_("Families"),
    requires={Project.asset_directories.require(RASPBERRY_MINT)},
)
class Families(Template, Manufacturable):
    """
    A person's families.

    .. plugin:: content:raspberry-mint-families
    """

    @override
    @Project.require
    @classmethod
    async def new(cls, project: Project, /) -> Self:
        return cls(jinja=await project.jinja)

    @override
    async def build_template(self, document: Document) -> TemplateBuild:
        if isinstance(document.resource, Person):
            return "component/raspberry-mint/families.html.j2", {
                "person": document.resource,
                "person_descendant_families": person_descendant_families(
                    document.resource
                ),
            }
        return None
