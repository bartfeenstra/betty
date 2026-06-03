"""
The speaker role.
"""

from typing import final

from betty.locale.localizable.gettext import _, ngettext
from betty.role import Role, RoleDefinition


@final
@RoleDefinition(
    "speaker",
    label=_("Speaker"),
    label_plural=_("Speakers"),
    label_countable=ngettext("{count} speaker", "{count} speakers"),
    description=_("Someone performed public speaking at the event."),
)
class Speaker(Role):
    """
    .. plugin:: role:speaker.
    """
