"""
The attendee role.
"""

from typing import final

from betty.locale.localizable.gettext import _, ngettext
from betty.role import Role, RoleDefinition


@final
@RoleDefinition(
    "attendee",
    label=_("Attendee"),
    label_plural=_("Attendees"),
    label_countable=ngettext("{count} attendee", "{count} attendees"),
)
class Attendee(Role):
    """
    .. plugin:: role:attendee.
    """
