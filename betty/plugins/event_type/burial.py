"""
The burial event type.
"""

from __future__ import annotations

from typing import final

from betty.event_type import EventType, EventTypeDefinition
from betty.locale.localizable.gettext import _, ngettext
from betty.plugins.event_type.death import Death


@final
@EventTypeDefinition(
    "burial",
    label=_("Burial"),
    label_plural=_("Burials"),
    label_countable=ngettext("{count} burial", "{count} burials"),
    after={Death},
    indicates=Death,
)
class Burial(EventType):
    """
    .. plugin:: event-type:burial.
    """
