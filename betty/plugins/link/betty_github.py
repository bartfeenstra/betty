"""
The link to Betty's GitHub.
"""

from typing import final

from betty.html import NavigationLink
from betty.link import Link, LinkDefinition
from betty.locale.localizable.gettext import _


@final
@LinkDefinition(
    "betty-github",
    link=NavigationLink(
        "https://github.com/bartfeenstra/betty", _("Find Betty on GitHub")
    ),
)
class BettyGithub(Link):
    """
    .. plugin:: link:betty-github.
    """
