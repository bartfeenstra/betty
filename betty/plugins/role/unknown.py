"""
The unknown role.
"""

from typing import final

from betty.classtools import Singleton
from betty.locale.localizable.gettext import _, ngettext
from betty.role import Role, RoleDefinition


@final
@RoleDefinition(
    "unknown",
    label=_("Unknown"),
    label_plural=_("Unknowns"),
    label_countable=ngettext("{count} unknown", "{count} unknowns"),
)
class Unknown(Role, Singleton):
    """
    .. plugin:: role:unknown.
    """
