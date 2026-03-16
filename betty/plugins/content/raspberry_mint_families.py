"""
The families content plugin.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from betty.content import ContentDefinition
from betty.locale.localizable.gettext import _
from betty.plugins.content.template import Template, TemplateBuild
from betty.plugins.entity.person import Person
from betty.service.factory import Manufacturable
from betty.service.requirement.project import require_project

if TYPE_CHECKING:
    from betty.document import Document
    from betty.project import Project


@final
@ContentDefinition("raspberry-mint-families", label=_("Families"))
class Families(Template, Manufacturable):
    """
    A person's families.

    .. plugin:: content:raspberry-mint-families
    """

    @override
    @classmethod
    @require_project
    async def new(cls, project: Project, /) -> Self:
        return cls(jinja=await project.jinja)

    @override
    async def build_template(self, document: Document) -> TemplateBuild:
        if isinstance(document.resource, Person):
            return "component/raspberry-mint/families.html.j2", {
                "person": document.resource,
            }
        return None
