"""
The marriage event type.
"""

from __future__ import annotations

from typing import final

from betty.event_type import EventType, EventTypeDefinition
from betty.locale.localizable.gettext import _, ngettext
from betty.plugins.event_type.birth import Birth
from betty.plugins.event_type.death import Death
from betty.plugins.event_type.engagement import Engagement


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
