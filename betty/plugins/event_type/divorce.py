"""
The divorce event type.
"""

from __future__ import annotations

from typing import final

from betty.event_type import EventType, EventTypeDefinition
from betty.locale.localizable.gettext import _, ngettext
from betty.plugins.event_type.birth import Birth
from betty.plugins.event_type.death import Death
from betty.plugins.event_type.marriage import Marriage


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
