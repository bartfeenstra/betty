"""
The celebrant role.
"""

from typing import final

from betty.locale.localizable.gettext import _, ngettext
from betty.role import Role, RoleDefinition


@final
@RoleDefinition(
    "celebrant",
    label=_("Celebrant"),
    label_plural=_("Celebrants"),
    label_countable=ngettext("{count} celebrant", "{count} celebrants"),
)
class Celebrant(Role):
    """
    .. plugin:: role:celebrant.

    Someone was the `celebrant <https://en.wikipedia.org/wiki/Officiant>`_ at the event.

    This includes but is not limited to:

    - civil servant
    - religious leader
    - civilian
    """
