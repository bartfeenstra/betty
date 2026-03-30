"""
The link to Betty's documentation.
"""

from typing import final

from betty.link import Link, LinkDefinition, StaticLink
from betty.locale.localizable.gettext import _


@final
@LinkDefinition(
    "betty-documentation",
    link=StaticLink("https://betty.readthedocs.io/", _("Read the Betty documentation")),
)
class BettyDocumentation(Link):
    """
    .. plugin:: link:betty-documentation.
    """
