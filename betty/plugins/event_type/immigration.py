"""
The immigration event type.
"""

from __future__ import annotations

from typing import final

from betty.event_type import EventType, EventTypeDefinition
from betty.locale.localizable.gettext import _, ngettext
from betty.plugins.event_type.birth import Birth
from betty.plugins.event_type.death import Death


@final
@EventTypeDefinition(
    "immigration",
    label=_("Immigration"),
    label_plural=_("Immigrations"),
    label_countable=ngettext("{count} immigration", "{count} immigrations"),
    after={Birth},
    before={Death},
)
class Immigration(EventType):
    """
    .. plugin:: event-type:immigration.
    """
