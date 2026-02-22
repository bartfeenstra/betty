"""
Contents for the demonstration site.
"""

from typing import Self, override

from betty.content import ContentDefinition
from betty.content.contents import Template, TemplateBuild
from betty.document import Document
from betty.project import Project
from betty.service.factory import Manufacturable
from betty.service.requirement.project import require_project


@ContentDefinition(
    "-demo-incomplete-translation-warning", label="Incomplete translation warning"
)
class _IncompleteTranslationWarning(Template, Manufacturable):
    @override
    @classmethod
    @require_project
    async def new(cls, project: Project, /) -> Self:
        return cls(jinja=await project.jinja)

    @override
    async def build_template(self, document: Document) -> TemplateBuild:
        return "component/demo/-demo-incomplete-translation-warning.html.j2"
