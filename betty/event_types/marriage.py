"""
The marriage event type.
"""

from __future__ import annotations

from typing import final

from betty.event_type import EventType, EventTypeDefinition
from betty.event_types.birth import Birth
from betty.event_types.death import Death
from betty.event_types.engagement import Engagement
from betty.locale.localizable.gettext import _, ngettext


@final
@EventTypeDefinition(
    "marriage",
    label=_("Marriage"),
    label_plural=_("Marriages"),
    label_countable=ngettext("{count} marriage", "{count} marriages"),
    after={Birth, Engagement},
    before={Death},
)
class Marriage(EventType):
    """
    .. plugin:: event-type:marriage.
    """
