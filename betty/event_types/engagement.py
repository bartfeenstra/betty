"""
The engagement event type.
"""

from __future__ import annotations

from typing import final

from betty.event_type import EventType, EventTypeDefinition
from betty.event_types.birth import Birth
from betty.event_types.death import Death
from betty.locale.localizable.gettext import _, ngettext


@final
@EventTypeDefinition(
    "engagement",
    label=_("Engagement"),
    label_plural=_("Engagements"),
    label_countable=ngettext("{count} engagement", "{count} engagements"),
    after={Birth},
    before={Death},
)
class Engagement(EventType):
    """
    .. plugin:: event-type:engagement.
    """
