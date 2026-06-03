"""
The organizer role.
"""

from typing import final

from betty.locale.localizable.gettext import _, ngettext
from betty.role import Role, RoleDefinition


@final
@RoleDefinition(
    "organizer",
    label=_("Organizer"),
    label_plural=_("Organizers"),
    label_countable=ngettext("{count} organizer", "{count} organizers"),
)
class Organizer(Role):
    """
    .. plugin:: role:organizer.
    """
