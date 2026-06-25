"""
The burial event type.
"""

from __future__ import annotations

from typing import final

from betty.event_type import EventType, EventTypeDefinition
from betty.event_types.death import Death
from betty.localizables.gettext import _, ngettext


@final
@EventTypeDefinition(
    "burial",
    label=_("Burial"),
    label_plural=_("Burials"),
    label_countable=ngettext("{count} burial", "{count} burials"),
    after={Death},
)
class Burial(EventType):
    """
    .. plugin:: event-type:burial.
    """
