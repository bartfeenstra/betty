"""
The emigration event type.
"""

from __future__ import annotations

from typing import final

from betty.event_type import EventType, EventTypeDefinition
from betty.event_types.birth import Birth
from betty.event_types.death import Death
from betty.localizables.gettext import _, ngettext


@final
@EventTypeDefinition(
    "emigration",
    label=_("Emigration"),
    label_plural=_("Emigrations"),
    label_countable=ngettext("{count} emigration", "{count} emigrations"),
    after={Birth},
    before={Death},
)
class Emigration(EventType):
    """
    .. plugin:: event-type:emigration.
    """
