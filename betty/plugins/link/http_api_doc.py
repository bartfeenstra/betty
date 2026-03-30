"""
The link to the HTTP API documentation.
"""

from typing import final

from betty.link import Link, LinkDefinition, StaticLink
from betty.locale.localizable.gettext import _


@final
@LinkDefinition(
    "http-api-doc",
    link=StaticLink("betty-static:///api/index.html", _("API documentation")),
)
class HttpApiDoc(Link):
    """
    .. plugin:: link:http-api-doc.
    """
