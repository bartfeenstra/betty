"""
The families content plugin.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from betty.content import ContentDefinition
from betty.locale.localizable.gettext import _
from betty.plugins.asset.raspberry_mint import RASPBERRY_MINT
from betty.plugins.content.template import Template, TemplateBuild
from betty.plugins.entity.person import Person
from betty.plugins.extension._theme import person_descendant_families
from betty.project import Project
from betty.service.factory import Manufacturable

if TYPE_CHECKING:
    from betty.document import Document


@final
@ContentDefinition(
    "raspberry-mint-families",
    label=_("Families"),
    requires={Project.assets.require(RASPBERRY_MINT)},
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
