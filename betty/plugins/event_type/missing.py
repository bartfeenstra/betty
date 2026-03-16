"""
The missing event type.
"""

from __future__ import annotations

from typing import final

from betty.event_type import EventType, EventTypeDefinition
from betty.locale.localizable.gettext import _, ngettext
from betty.plugins.event_type.birth import Birth
from betty.plugins.event_type.death import Death


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
