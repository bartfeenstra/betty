"""
The baptism event type.
"""

from __future__ import annotations

from typing import final

from betty.event_type import EventType, EventTypeDefinition
from betty.event_types.birth import Birth
from betty.event_types.death import Death
from betty.locale.localizable.gettext import _, ngettext


@final
@EventTypeDefinition(
    "baptism",
    label=_("Baptism"),
    label_plural=_("Baptisms"),
    label_countable=ngettext("{count} baptism", "{count} baptisms"),
    after={Birth},
    before={Death},
    indicates=Birth,
)
class Baptism(EventType):
    """
    .. plugin:: event-type:baptism.
    """
