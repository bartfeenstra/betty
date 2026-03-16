"""
The residence event type.
"""

from __future__ import annotations

from typing import final

from betty.event_type import EventType, EventTypeDefinition
from betty.locale.localizable.gettext import _, ngettext
from betty.plugins.event_type.birth import Birth
from betty.plugins.event_type.death import Death


@final
@EventTypeDefinition(
    "residence",
    label=_("Residence"),
    label_plural=_("Residences"),
    label_countable=ngettext("{count} residence", "{count} residences"),
    after={Birth},
    before={Death},
)
class Residence(EventType):
    """
    .. plugin:: event-type:residence.
    """
