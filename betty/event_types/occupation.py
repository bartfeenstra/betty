"""
The occupation event type.
"""

from __future__ import annotations

from typing import final

from betty.event_type import EventType, EventTypeDefinition
from betty.event_types.birth import Birth
from betty.event_types.death import Death
from betty.locale.localizable.gettext import _, ngettext


@final
@EventTypeDefinition(
    "occupation",
    label=_("Occupation"),
    label_plural=_("Occupations"),
    label_countable=ngettext("{count} occupation", "{count} occupations"),
    after={Birth},
    before={Death},
)
class Occupation(EventType):
    """
    .. plugin:: event-type:occupation.
    """
