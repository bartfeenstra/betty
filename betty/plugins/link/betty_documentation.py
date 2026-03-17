"""
The link to Betty's documentation.
"""

from typing import final

from betty.html import NavigationLink
from betty.link import Link, LinkDefinition
from betty.locale.localizable.gettext import _


@final
@LinkDefinition(
    "betty-documentation",
    link=NavigationLink(
        "https://betty.readthedocs.io/", _("Read the Betty documentation")
    ),
)
class BettyDocumentation(Link):
    """
    .. plugin:: link:betty-documentation.
    """
