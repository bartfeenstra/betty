"""
The divorce event type.
"""

from __future__ import annotations

from typing import final

from betty.event_type import EventType, EventTypeDefinition
from betty.event_types.birth import Birth
from betty.event_types.death import Death
from betty.event_types.marriage import Marriage
from betty.locale.localizable.gettext import _, ngettext


@final
@EventTypeDefinition(
    "divorce",
    label=_("Divorce"),
    label_plural=_("Divorces"),
    label_countable=ngettext("{count} divorce", "{count} divorces"),
    after={Birth, Marriage},
    before={Death},
)
class Divorce(EventType):
    """
    .. plugin:: event-type:divorce.
    """
