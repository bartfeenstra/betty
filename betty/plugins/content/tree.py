"""
The interactive family tree content plugin.
"""

from typing import Self, final, override

from betty.asset_directories.trees import TREES
from betty.content import ContentDefinition
from betty.document import Document
from betty.entities.person import Person
from betty.extensions.webpack import Webpack
from betty.factory import Manufacturable
from betty.jinja_filters.webpack_entry_point_js import WebpackEntryPointJs
from betty.locale.localizable.gettext import _
from betty.plugins.content.template import Template, TemplateBuild
from betty.project import Project


@final
@ContentDefinition(
    "tree",
    label=_("Family tree"),
    requires={
        Project.asset_directories.require(TREES),
        Project.extensions.require(Webpack),
        Project.jinja_filters.require(WebpackEntryPointJs),
    },
)
class Tree(Template, Manufacturable):
    """
    An interactive family tree.

    .. plugin:: content:tree
    """

    @override
    @Project.require
    @classmethod
    async def new(cls, project: Project, /) -> Self:
        return cls(jinja=await project.jinja)

    @override
    async def build_template(self, document: Document) -> TemplateBuild:
        if isinstance(document.resource, Person):
            return "component/trees/tree.html.j2", {
                "person": document.resource,
            }
        return None
