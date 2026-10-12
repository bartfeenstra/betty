"""
The unknown event type.
"""

from __future__ import annotations

from typing import final

from betty.event_type import EventType, EventTypeDefinition
from betty.frosties.classtools import Frozen
from betty.localizables.gettext import _, ngettext


@final
@EventTypeDefinition(
    "unknown",
    label=_("Unknown"),
    label_plural=_("Unknowns"),
    label_countable=ngettext("{count} unknown", "{count} unknowns"),
)
class UnknownEventType(EventType, Frozen):
    """
    .. plugin:: event-type:unknown.
    """
