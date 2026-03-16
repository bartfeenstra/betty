"""
The will event type.
"""

from __future__ import annotations

from typing import final

from betty.event_type import EventType, EventTypeDefinition
from betty.locale.localizable.gettext import _, ngettext
from betty.plugins.event_type.death import Death


@final
@EventTypeDefinition(
    "will",
    label=_("Will"),
    label_plural=_("Wills"),
    label_countable=ngettext("{count} will", "{count} wills"),
    after={Death},
)
class Will(EventType):
    """
    .. plugin:: event-type:will.
    """
