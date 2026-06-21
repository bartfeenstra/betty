"""
The unknown role.
"""

from __future__ import annotations

from typing import final

from betty.classtools import Singleton
from betty.localizables.gettext import _, ngettext
from betty.role import Role, RoleDefinition


@final
@RoleDefinition(
    "unknown",
    label=_("Unknown"),
    label_plural=_("Unknowns"),
    label_countable=ngettext("{count} unknown", "{count} unknowns"),
)
class UnknownRole(Role, Singleton):
    """
    .. plugin:: role:unknown.
    """
