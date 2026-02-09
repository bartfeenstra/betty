"""
Content providers for the demonstration site.
"""

from typing import Self

from typing_extensions import override

from betty.content_provider import ContentProviderDefinition
from betty.content_provider.content_providers import ProvidedTemplate, Template
from betty.document import Document
from betty.project import Project
from betty.service.factory import Manufacturable
from betty.service.requirement.project import require_project


@ContentProviderDefinition(
    "-demo-incomplete-translation-warning", label="Incomplete translation warning"
)
class _IncompleteTranslationWarning(Template, Manufacturable):
    @override
    @classmethod
    @require_project
    async def new(cls, project: Project, /) -> Self:
        return cls(jinja=await project.jinja)

    @override
    async def provide_template(self, document: Document) -> ProvidedTemplate:
        return "component/demo/-demo-incomplete-translation-warning.html.j2"
