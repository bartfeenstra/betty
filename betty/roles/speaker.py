"""
The speaker role.
"""

from __future__ import annotations

from typing import final

from betty.localizables.gettext import _, ngettext
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
