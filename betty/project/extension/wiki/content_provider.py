"""
Dynamic content.
"""

from betty.content_provider import ContentProviderDefinition
from betty.content_provider.content_providers import Template
from betty.locale.localizable import _
from betty.project.extension.wiki import Wiki


@ContentProviderDefinition(
    id="wiki-wikipedia-summary",
    label=_("Wikipedia summary"),
    depends_on_extensions={Wiki},
)
class WikipediaSummary(Template):
    """
    A Wikipedia summary.
    """
