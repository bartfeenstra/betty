"""
The retirement event type.
"""

from __future__ import annotations

from typing import final

from betty.event_type import EventType, EventTypeDefinition
from betty.event_types.birth import Birth
from betty.event_types.death import Death
from betty.locale.localizable.gettext import _, ngettext


@final
@EventTypeDefinition(
    "retirement",
    label=_("Retirement"),
    label_plural=_("Retirements"),
    label_countable=ngettext("{count} retirement", "{count} retirements"),
    after={Birth},
    before={Death},
)
class Retirement(EventType):
    """
    .. plugin:: event-type:retirement.
    """
