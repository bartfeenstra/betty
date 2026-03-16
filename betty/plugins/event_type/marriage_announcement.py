"""
The marriage announcement event type.
"""

from __future__ import annotations

from typing import final

from betty.event_type import EventType, EventTypeDefinition
from betty.locale.localizable.gettext import _, ngettext
from betty.plugins.event_type.birth import Birth
from betty.plugins.event_type.death import Death
from betty.plugins.event_type.marriage import Marriage


@final
@EventTypeDefinition(
    "marriage-announcement",
    label=_("Announcement of marriage"),
    label_plural=_("Announcements of marriage"),
    label_countable=ngettext(
        "{count} announcement of marriage", "{count} announcements of marriage"
    ),
    after={Birth},
    before={Death, Marriage},
)
class MarriageAnnouncement(EventType):
    """
    .. plugin:: event-type:marriage-announcement.
    """
