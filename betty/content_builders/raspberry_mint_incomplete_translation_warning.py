"""
The incomplete translation warning content plugin.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from betty.asset_directories.raspberry_mint import raspberry_mint
from betty.content_builder import ContentBuilderDefinition
from betty.content_builders.template import Template, TemplateBuild
from betty.factory import Manufacturable
from betty.project import Project

if TYPE_CHECKING:
    from betty.document import Document


@final
@ContentBuilderDefinition(
    "raspberry-mint-incomplete-translation-warning",
    label="Incomplete translation warning",
    requires={Project.asset_directories.require(raspberry_mint)},
)
class IncompleteTranslationWarning(Template, Manufacturable):
    """
    .. plugin:: content-builder:raspberry-mint-incomplete-translation-warning.
    """

    @override
    @Project.require
    @classmethod
    async def new(cls, project: Project, /) -> Self:
        return cls(jinja=await project.jinja)

    @override
    async def build_template(self, document: Document) -> TemplateBuild:
        return "component/raspberry-mint/incomplete-translation-warning.html.j2"
