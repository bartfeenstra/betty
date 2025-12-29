"""
Dynamic content.
"""

from typing import Self

from typing_extensions import override

from betty.content_provider import ContentProviderDefinition
from betty.content_provider.content_providers import Template
from betty.locale.localizable.gettext import _
from betty.project import Project
from betty.project.extension.wiki import Wiki
from betty.project.factory import ProjectDependentSelfFactory
from betty.requirement import HasRequirement, Requirement
from betty.service.level import ServiceLevel


@ContentProviderDefinition("wiki-wikipedia-summary", label=_("Wikipedia summary"))
class WikipediaSummary(Template, ProjectDependentSelfFactory, HasRequirement):
    """
    A Wikipedia summary.
    """

    @override
    @classmethod
    async def new_for_project(cls, project: Project) -> Self:
        return cls(jinja2_environment=await project.jinja2_environment)

    @override
    @classmethod
    async def requirement(cls, services: ServiceLevel, /) -> Requirement | None:
        return await Wiki.requirement_for(
            services, cls.plugin().reference_label_with_type
        )
