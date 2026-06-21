"""
The funeral event type.
"""

from __future__ import annotations

from typing import final

from betty.event_type import EventType, EventTypeDefinition
from betty.event_types.death import Death
from betty.localizables.gettext import _, ngettext


@final
@EventTypeDefinition(
    "funeral",
    label=_("Funeral"),
    label_plural=_("Funerals"),
    label_countable=ngettext("{count} funeral", "{count} funerals"),
    after={Death},
    indicates=Death,
)
class Funeral(EventType):
    """
    .. plugin:: event-type:funeral.
    """
