"""
Content providers for the demonstration site.
"""

from typing import Self

from typing_extensions import override

from betty.content_provider import ContentProviderDefinition
from betty.content_provider.content_providers import Template
from betty.project import Project
from betty.project.factory import ProjectDependentSelfFactory


@ContentProviderDefinition(
    "-demo-incomplete-translation-warning", label="Incomplete translation warning"
)
class _IncompleteTranslationWarning(Template, ProjectDependentSelfFactory):
    @override
    @classmethod
    async def new_for_project(cls, project: Project) -> Self:
        return cls(jinja2_environment=await project.jinja2_environment)
