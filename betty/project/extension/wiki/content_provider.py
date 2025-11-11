"""
Dynamic content.
"""

from betty.content_provider import ContentProviderDefinition
from betty.content_provider.content_providers import Jinja2TemplateContentProvider
from betty.locale.localizable import _


@ContentProviderDefinition(
    id="wiki-wikipedia-summary",
    label=_("Wikipedia summary"),
)
class WikipediaSummary(Jinja2TemplateContentProvider):
    """
    A Wikipedia summary.
    """

    _template = "wiki/wikipedia-summary.html.j2"
