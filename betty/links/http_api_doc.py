"""
The link to the HTTP API documentation.
"""

from __future__ import annotations

from typing import Final

from betty.link import LinkDefinition, StaticLink
from betty.locale.localizable.gettext import _

HTTP_API_DOC: Final[LinkDefinition] = LinkDefinition(
    "http-api-doc",
    link=StaticLink("betty-static:///api/index.html", _("API documentation")),
)
