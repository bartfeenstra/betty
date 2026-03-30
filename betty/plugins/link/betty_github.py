"""
The link to Betty's GitHub.
"""

from typing import final

from betty.link import Link, LinkDefinition, StaticLink
from betty.locale.localizable.gettext import _


@final
@LinkDefinition(
    "betty-github",
    link=StaticLink("https://github.com/bartfeenstra/betty", _("Find Betty on GitHub")),
)
class BettyGithub(Link):
    """
    .. plugin:: link:betty-github.
    """
