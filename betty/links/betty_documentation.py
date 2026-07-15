"""
The link to Betty's documentation.
"""

from __future__ import annotations

from typing import Final

from betty import about
from betty.link import LinkDefinition, StaticLink
from betty.localizables.gettext import _

BETTY_DOCUMENTATION: Final[LinkDefinition] = LinkDefinition(
    "betty-documentation",
    link=StaticLink(about.url_documentation, _("Read the Betty documentation")),
)
