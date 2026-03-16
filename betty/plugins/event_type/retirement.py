"""
The retirement event type.
"""

from __future__ import annotations

from typing import final

from betty.event_type import EventType, EventTypeDefinition
from betty.locale.localizable.gettext import _, ngettext
from betty.plugins.event_type.birth import Birth
from betty.plugins.event_type.death import Death


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
