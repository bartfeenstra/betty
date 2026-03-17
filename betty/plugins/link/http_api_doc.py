"""
The link to the HTTP API documentation.
"""

from typing import final

from betty.html import NavigationLink
from betty.link import Link, LinkDefinition
from betty.locale.localizable.gettext import _


@final
@LinkDefinition(
    "http-api-doc",
    link=NavigationLink("betty-static:///api/index.html", _("API documentation")),
)
class HttpApiDoc(Link):
    """
    .. plugin:: link:http-api-doc.
    """
