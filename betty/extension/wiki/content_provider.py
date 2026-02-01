"""
Dynamic content.
"""

from typing import Self

from typing_extensions import override

from betty.content_provider import ContentProviderDefinition
from betty.content_provider.content_providers import Template
from betty.extension.wiki import Wiki
from betty.locale.localizable.gettext import _
from betty.service.level.factory import ServiceLevelDependentSelfFactory
from betty.service.requirement import require_extension


@ContentProviderDefinition("wiki-wikipedia-summary", label=_("Wikipedia summary"))
class WikipediaSummary(Template, ServiceLevelDependentSelfFactory):
    """
    A Wikipedia summary.

    .. plugin:: content-provider:wiki-wikipedia-summary
    """

    @override
    @classmethod
    @require_extension(Wiki)
    async def new_for_services(cls, *, extension: Wiki) -> Self:
        return cls(jinja2_environment=await extension._project.jinja2_environment)
