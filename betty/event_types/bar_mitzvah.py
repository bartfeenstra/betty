"""
The bar mitzvah event type.
"""

from __future__ import annotations

from typing import final

from betty.event_type import EventType, EventTypeDefinition
from betty.event_types.birth import Birth
from betty.event_types.death import Death
from betty.locale.localizable.gettext import _, ngettext


@final
@EventTypeDefinition(
    "bar-mitzvah",
    label=_("Bar mitzvah"),
    label_plural=_("Bar mitzvahs"),
    label_countable=ngettext("{count} bar mitzvah", "{count} bar mitzvahs"),
    after={Birth},
    before={Death},
    indicates=Birth,
)
class BarMitzvah(EventType):
    """
    .. plugin:: event-type:bar-mitzvah.
    """
