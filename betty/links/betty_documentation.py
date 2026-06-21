"""
The link to Betty's documentation.
"""

from __future__ import annotations

from typing import Final

from betty.link import LinkDefinition, StaticLink
from betty.locale.localizable.gettext import _

BETTY_DOCUMENTATION: Final[LinkDefinition] = LinkDefinition(
    "betty-documentation",
    link=StaticLink("https://betty.readthedocs.io/", _("Read the Betty documentation")),
)
