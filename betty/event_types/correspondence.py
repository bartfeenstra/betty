"""
The correspondence event type.
"""

from __future__ import annotations

from typing import final

from betty.event_type import EventType, EventTypeDefinition
from betty.locale.localizable.gettext import _, ngettext


@final
@EventTypeDefinition(
    "correspondence",
    label=_("Correspondence"),
    label_plural=_("Correspondences"),
    label_countable=ngettext("{count} correspondence", "{count} correspondences"),
)
class Correspondence(EventType):
    """
    .. plugin:: event-type:correspondence.
    """
