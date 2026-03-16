"""
The divorce announcement event type.
"""

from __future__ import annotations

from typing import final

from betty.event_type import EventType, EventTypeDefinition
from betty.locale.localizable.gettext import _, ngettext
from betty.plugins.event_type.birth import Birth
from betty.plugins.event_type.death import Death
from betty.plugins.event_type.divorce import Divorce
from betty.plugins.event_type.marriage import Marriage


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
