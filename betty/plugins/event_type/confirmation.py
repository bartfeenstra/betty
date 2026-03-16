"""
The confirmation event type.
"""

from __future__ import annotations

from typing import final

from betty.event_type import EventType, EventTypeDefinition
from betty.locale.localizable.gettext import _, ngettext
from betty.plugins.event_type.birth import Birth
from betty.plugins.event_type.death import Death


@final
@EventTypeDefinition(
    "confirmation",
    label=_("Confirmation"),
    label_plural=_("Confirmations"),
    label_countable=ngettext("{count} confirmation", "{count} confirmations"),
    after={Birth},
    before={Death},
)
class Confirmation(EventType):
    """
    .. plugin:: event-type:confirmation.
    """
