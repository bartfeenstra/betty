"""
The residence event type.
"""

from __future__ import annotations

from typing import final

from betty.event_type import EventType, EventTypeDefinition
from betty.event_types.birth import Birth
from betty.event_types.death import Death
from betty.localizables.gettext import _, ngettext


@final
@EventTypeDefinition(
    "residence",
    label=_("Residence"),
    label_plural=_("Residences"),
    label_countable=ngettext("{count} residence", "{count} residences"),
    after={Birth},
    before={Death},
)
class Residence(EventType):
    """
    .. plugin:: event-type:residence.
    """
