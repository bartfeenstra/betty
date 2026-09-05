"""
The families content plugin.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from betty.asset_directories.raspberry_mint import raspberry_mint
from betty.content_builder import ContentBuilderDefinition
from betty.content_builders.template import Template, TemplateBuild
from betty.entities.person import Person
from betty.factory import Arg1Manufacturable
from betty.localizables.gettext import _
from betty.project import Project
from betty.service_providers._theme import person_descendant_families

if TYPE_CHECKING:
    from betty.document import Document


@final
@ContentBuilderDefinition(
    "raspberry-mint-families",
    label=_("Families"),
    requires={Project.asset_directories.require(raspberry_mint)},
)
class Families(Template, Arg1Manufacturable[Project]):
    """
    A person's families.

    .. plugin:: content-builder:raspberry-mint-families
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
