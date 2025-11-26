"""
Dynamic content.
"""

from betty.content_provider import ContentProviderPlugin
from betty.content_provider.content_providers import Template


@ContentProviderPlugin(
    "-demo-front-page-content", label="Demo site front page content (private)"
)
class _FrontPageContent(Template):
    pass
