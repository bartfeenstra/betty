"""
The occupation event type.
"""

from __future__ import annotations

from typing import final

from betty.event_type import EventType, EventTypeDefinition
from betty.locale.localizable.gettext import _, ngettext
from betty.plugins.event_type.birth import Birth
from betty.plugins.event_type.death import Death


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
