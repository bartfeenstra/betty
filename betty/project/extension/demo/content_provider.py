"""
Dynamic content.
"""

from betty.content_provider import ContentProviderDefinition
from betty.content_provider.content_providers import Template
from betty.locale.localizable import Plain


@ContentProviderDefinition(
    id="-demo-front-page-content",
    label=Plain("Front page content (demo)"),
)
class _FrontPageContent(Template):
    pass


@ContentProviderDefinition(
    id="-demo-front-page-summary",
    label=Plain("Front page summary (demo)"),
)
class _FrontPageSummary(Template):
    pass
