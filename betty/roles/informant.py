"""
The informant role.
"""

from typing import final

from betty.locale.localizable.gettext import _, ngettext
from betty.role import Role, RoleDefinition


@final
@RoleDefinition(
    "informant",
    label=_("Informant"),
    label_plural=_("Informants"),
    label_countable=ngettext("{count} informant", "{count} informants"),
    description=_("Someone reported the event with a record-keeping institution."),
)
class Informant(Role):
    """
    .. plugin:: role:informant.
    """
