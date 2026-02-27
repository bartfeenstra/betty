"""
Tree content.
"""

from typing import Self, override

from betty.ancestry.person import Person
from betty.content import ContentDefinition
from betty.content.contents import Template, TemplateBuild
from betty.document import Document
from betty.locale.localizable.gettext import _
from betty.project import Project
from betty.service.factory import Manufacturable
from betty.service.requirement.project import require_project


@ContentDefinition("trees-tree", label=_("Family tree"))
class Tree(Template, Manufacturable):
    """
    An interactive family tree.

    .. plugin:: content:trees-tree
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
