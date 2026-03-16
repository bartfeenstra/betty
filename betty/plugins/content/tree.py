"""
The interactive family tree content plugin.
"""

from typing import Self, final, override

from betty.content import ContentDefinition
from betty.document import Document
from betty.locale.localizable.gettext import _
from betty.plugins.content.template import Template, TemplateBuild
from betty.plugins.entity.person import Person
from betty.project import Project
from betty.service.factory import Manufacturable
from betty.service.requirement.project import require_project


@final
@ContentDefinition("tree", label=_("Family tree"))
class Tree(Template, Manufacturable):
    """
    An interactive family tree.

    .. plugin:: content:tree
    """

    @override
    @classmethod
    @require_project
    async def new(cls, project: Project, /) -> Self:
        return cls(jinja=await project.jinja)

    @override
    async def build_template(self, document: Document) -> TemplateBuild:
        if isinstance(document.resource, Person):
            return "component/trees/tree.html.j2", {
                "person": document.resource,
            }
        return None
