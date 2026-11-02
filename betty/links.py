"""
Link plugins.
"""

from __future__ import annotations

from typing import Final

from betty import about
from betty.link import LinkDefinition, StaticLink
from betty.localizables.gettext import _

betty_documentation: Final[LinkDefinition] = LinkDefinition(
    "betty-documentation",
    link=StaticLink(about.url_documentation, _("Read the Betty documentation")),
)

betty_github: Final[LinkDefinition] = LinkDefinition(
    "betty-github", link=StaticLink(about.url_code, _("Find Betty on GitHub"))
)
