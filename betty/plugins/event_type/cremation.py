"""
The cremation event type.
"""

from __future__ import annotations

from typing import final

from betty.event_type import EventType, EventTypeDefinition
from betty.locale.localizable.gettext import _, ngettext
from betty.plugins.event_type.death import Death


@final
@EventTypeDefinition(
    "cremation",
    label=_("Cremation"),
    label_plural=_("Cremations"),
    label_countable=ngettext("{count} cremation", "{count} cremations"),
    after={Death},
    indicates=Death,
)
class Cremation(EventType):
    """
    .. plugin:: event-type:cremation.
    """
