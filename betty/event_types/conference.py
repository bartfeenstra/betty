"""
The conference event type.
"""

from __future__ import annotations

from typing import final

from betty.event_type import EventType, EventTypeDefinition
from betty.event_types.birth import Birth
from betty.event_types.death import Death
from betty.locale.localizable.gettext import _, ngettext


@final
@EventTypeDefinition(
    "conference",
    label=_("Conference"),
    label_plural=_("Conferences"),
    label_countable=ngettext("{count} conference", "{count} conferences"),
    before={Death},
    after={Birth},
)
class Conference(EventType):
    """
    .. plugin:: event-type:conference.
    """
