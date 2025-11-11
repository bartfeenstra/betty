"""
Dynamic content.
"""

from betty.content_provider import ContentProviderDefinition
from betty.content_provider.content_providers import (
    Jinja2TemplateContentProvider,
)
from betty.locale.localizable import Plain


@ContentProviderDefinition(
    id="demo-front-page-content",
    label=Plain("Front page content (demo)"),
)
class _FrontPageContent(Jinja2TemplateContentProvider):
    _template = "demo-front-page-content.html.j2"


@ContentProviderDefinition(
    id="demo-front-page-summary",
    label=Plain("Front page summary (demo)"),
)
class _FrontPageSummary(Jinja2TemplateContentProvider):
    _template = "demo-front-page-summary.html.j2"
