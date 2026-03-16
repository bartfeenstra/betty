"""
The emigration event type.
"""

from __future__ import annotations

from typing import final

from betty.event_type import EventType, EventTypeDefinition
from betty.locale.localizable.gettext import _, ngettext
from betty.plugins.event_type.birth import Birth
from betty.plugins.event_type.death import Death


@final
@EventTypeDefinition(
    "emigration",
    label=_("Emigration"),
    label_plural=_("Emigrations"),
    label_countable=ngettext("{count} emigration", "{count} emigrations"),
    after={Birth},
    before={Death},
)
class Emigration(EventType):
    """
    .. plugin:: event-type:emigration.
    """
