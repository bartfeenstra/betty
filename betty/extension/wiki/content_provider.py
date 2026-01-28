"""
Dynamic content.
"""

from typing import Self

from typing_extensions import override

from betty.content_provider import ContentProviderDefinition
from betty.content_provider.content_providers import Template
from betty.extension.wiki import Wiki
from betty.locale.localizable.gettext import _
from betty.project import Project
from betty.project.factory import require_project
from betty.requirement import HasRequirement, Requirement
from betty.service.level import ServiceLevel
from betty.service.level.factory import ServiceLevelDependentSelfFactory


@ContentProviderDefinition("wiki-wikipedia-summary", label=_("Wikipedia summary"))
class WikipediaSummary(Template, ServiceLevelDependentSelfFactory, HasRequirement):
    """
    A Wikipedia summary.
    """

    @override
    @classmethod
    @require_project
    async def new_for_services(cls, project: Project) -> Self:
        return cls(jinja2_environment=await project.jinja2_environment)

    @override
    @classmethod
    async def requirement(cls, services: ServiceLevel, /) -> Requirement | None:
        return await Wiki.requirement_for(
            services, cls.plugin().reference_label_with_type
        )
