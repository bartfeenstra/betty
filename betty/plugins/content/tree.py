"""
The interactive family tree content plugin.
"""

from typing import Self, final, override

from betty.content import ContentDefinition
from betty.document import Document
from betty.locale.localizable.gettext import _
from betty.plugins.asset.trees import Trees
from betty.plugins.content.template import Template, TemplateBuild
from betty.plugins.entity.person import Person
from betty.plugins.extension.webpack import Webpack
from betty.plugins.jinja_filter.webpack_entry_point_js import WebpackEntryPointJs
from betty.project import Project
from betty.service.factory import Manufacturable


@final
@ContentDefinition(
    "tree",
    label=_("Family tree"),
    requires={
        Project.assets.require(Trees),
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
