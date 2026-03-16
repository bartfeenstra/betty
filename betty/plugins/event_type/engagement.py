"""
The engagement event type.
"""

from __future__ import annotations

from typing import final

from betty.event_type import EventType, EventTypeDefinition
from betty.locale.localizable.gettext import _, ngettext
from betty.plugins.event_type.birth import Birth
from betty.plugins.event_type.death import Death


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
