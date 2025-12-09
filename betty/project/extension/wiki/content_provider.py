"""
Dynamic content.
"""

from typing_extensions import override

from betty.content_provider import ContentProviderDefinition
from betty.content_provider.content_providers import Template
from betty.locale.localizable.gettext import _
from betty.project.extension.wiki import Wiki
from betty.requirement import HasRequirement, Requirement
from betty.service.level import ServiceLevel


@ContentProviderDefinition("wiki-wikipedia-summary", label=_("Wikipedia summary"))
class WikipediaSummary(Template, HasRequirement):
    """
    A Wikipedia summary.
    """

    @override
    @classmethod
    async def requirement(cls, services: ServiceLevel, /) -> Requirement | None:
        return await Wiki.requirement_for(
            services, cls.plugin().reference_label_with_type
        )
