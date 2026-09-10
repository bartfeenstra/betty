"""
The interactive family tree content plugin.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from betty.asset_directories.trees import trees
from betty.content_builder import ContentBuilderDefinition
from betty.content_builders.template import Template, TemplateBuild
from betty.entities.person import Person
from betty.factory import Arg1Manufacturable
from betty.jinja_filters.webpack_entry_point_js import WebpackEntryPointJs
from betty.localizables.gettext import _
from betty.project import Project
from betty.service_providers.webpack import Webpack

if TYPE_CHECKING:
    from betty.document import Document


@final
@ContentBuilderDefinition(
    "tree",
    label=_("Family tree"),
    requires={
        Project.asset_directories.require(trees),
        Project.service_providers.require(Webpack),
        Project.jinja_filters.require(WebpackEntryPointJs),
    },
)
class Tree(Template, Arg1Manufacturable):
    """
    An interactive family tree.

    .. plugin:: content-builder:tree
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
