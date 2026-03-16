"""
The incomplete translation warning content plugin.
"""

from typing import Self, final, override

from betty.content import ContentDefinition
from betty.document import Document
from betty.plugins.content.template import Template, TemplateBuild
from betty.project import Project
from betty.service.factory import Manufacturable
from betty.service.requirement.project import require_project


@final
@ContentDefinition(
    "raspberry-mint-incomplete-translation-warning",
    label="Incomplete translation warning",
)
class IncompleteTranslationWarning(Template, Manufacturable):
    """
    .. plugin:: content:raspberry-mint-incomplete-translation-warning.
    """

    @override
    @classmethod
    @require_project
    async def new(cls, project: Project, /) -> Self:
        return cls(jinja=await project.jinja)

    @override
    async def build_template(self, document: Document) -> TemplateBuild:
        return "component/raspberry-mint/incomplete-translation-warning.html.j2"
