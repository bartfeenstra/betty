"""
The witness role.
"""

from typing import final

from betty.locale.localizable.gettext import _, ngettext
from betty.role import Role, RoleDefinition


@final
@RoleDefinition(
    "witness",
    label=_("Witness"),
    label_plural=_("Witnesses"),
    label_countable=ngettext("{count} witness", "{count} witnesses"),
    description=_("A formal witness to an event."),
)
class Witness(Role):
    """
    .. plugin:: role:witness.
    """
