"""
Content providers for the demonstration site.
"""

from typing import Self

from typing_extensions import override

from betty.content_provider import ContentProviderDefinition
from betty.content_provider.content_providers import Template
from betty.project import Project
from betty.project.factory import require_project
from betty.service.level.factory import ServiceLevelDependentSelfFactory


@ContentProviderDefinition(
    "-demo-incomplete-translation-warning", label="Incomplete translation warning"
)
class _IncompleteTranslationWarning(Template, ServiceLevelDependentSelfFactory):
    @override
    @classmethod
    @require_project
    async def new_for_services(cls, project: Project) -> Self:
        return cls(jinja2_environment=await project.jinja2_environment)
