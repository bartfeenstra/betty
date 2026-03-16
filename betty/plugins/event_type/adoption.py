"""
The adoption event type.
"""

from __future__ import annotations

from typing import final

from betty.event_type import EventType, EventTypeDefinition
from betty.locale.localizable.gettext import _, ngettext
from betty.plugins.event_type.birth import Birth
from betty.plugins.event_type.death import Death


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
