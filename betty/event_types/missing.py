"""
The missing event type.
"""

from __future__ import annotations

from typing import final

from betty.event_type import EventType, EventTypeDefinition
from betty.event_types.birth import Birth
from betty.event_types.death import Death
from betty.localizables.gettext import _, ngettext


@final
@EventTypeDefinition(
    "missing",
    label=_("Missing"),
    label_plural=_("Missings"),
    label_countable=ngettext("{count} missing", "{count} missings"),
    after={Birth},
    before={Death},
)
class Missing(EventType):
    """
    .. plugin:: event-type:missing.
    """
