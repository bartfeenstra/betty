"""
The divorce announcement event type.
"""

from __future__ import annotations

from typing import final

from betty.event_type import EventType, EventTypeDefinition
from betty.event_types.birth import Birth
from betty.event_types.death import Death
from betty.event_types.divorce import Divorce
from betty.event_types.marriage import Marriage
from betty.locale.localizable.gettext import _, ngettext


@final
@EventTypeDefinition(
    "divorce-announcement",
    label=_("Announcement of divorce"),
    label_plural=_("Announcements of divorce"),
    label_countable=ngettext(
        "{count} announcement of divorce", "{count} announcements of divorce"
    ),
    after={Birth, Marriage},
    before={Death, Divorce},
)
class DivorceAnnouncement(EventType):
    """
    .. plugin:: event-type:divorce-announcement.
    """
