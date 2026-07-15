"""
The link to Betty's GitHub.
"""

from __future__ import annotations

from typing import Final

from betty import about
from betty.link import LinkDefinition, StaticLink
from betty.localizables.gettext import _

BETTY_GITHUB: Final[LinkDefinition] = LinkDefinition(
    "betty-github",
    link=StaticLink(about.url_code, _("Find Betty on GitHub")),
)
