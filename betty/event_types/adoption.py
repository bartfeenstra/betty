"""
The adoption event type.
"""

from __future__ import annotations

from typing import final

from betty.event_type import EventType, EventTypeDefinition
from betty.event_types.birth import Birth
from betty.event_types.death import Death
from betty.locale.localizable.gettext import _, ngettext


@final
@EventTypeDefinition(
    "adoption",
    label=_("Adoption"),
    label_plural=_("Adoptions"),
    label_countable=ngettext("{count} adoption", "{count} adoptions"),
    after={Birth},
    before={Death},
)
class Adoption(EventType):
    """
    .. plugin:: event-type:adoption.
    """
