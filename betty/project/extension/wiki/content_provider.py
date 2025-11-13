"""
Dynamic content.
"""

from betty.content_provider import ContentProviderDefinition
from betty.content_provider.content_providers import Template
from betty.locale.localizable import _


@ContentProviderDefinition(
    id="wiki-wikipedia-summary",
    label=_("Wikipedia summary"),
)
class WikipediaSummary(Template):
    """
    A Wikipedia summary.
    """
