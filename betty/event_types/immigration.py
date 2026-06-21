"""
The immigration event type.
"""

from __future__ import annotations

from typing import final

from betty.event_type import EventType, EventTypeDefinition
from betty.event_types.birth import Birth
from betty.event_types.death import Death
from betty.localizables.gettext import _, ngettext


@final
@EventTypeDefinition(
    "immigration",
    label=_("Immigration"),
    label_plural=_("Immigrations"),
    label_countable=ngettext("{count} immigration", "{count} immigrations"),
    after={Birth},
    before={Death},
)
class Immigration(EventType):
    """
    .. plugin:: event-type:immigration.
    """
