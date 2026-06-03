"""
The link to Betty's GitHub.
"""

from typing import Final

from betty.link import LinkDefinition, StaticLink
from betty.locale.localizable.gettext import _

BETTY_GITHUB: Final[LinkDefinition] = LinkDefinition(
    "betty-github",
    link=StaticLink("https://github.com/bartfeenstra/betty", _("Find Betty on GitHub")),
)
