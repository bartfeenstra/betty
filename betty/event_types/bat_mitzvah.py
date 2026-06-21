"""
The bat mitzvah event type.
"""

from __future__ import annotations

from typing import final

from betty.event_type import EventType, EventTypeDefinition
from betty.event_types.birth import Birth
from betty.event_types.death import Death
from betty.localizables.gettext import _, ngettext


@final
@EventTypeDefinition(
    "bat-mitzvah",
    label=_("Bat mitzvah"),
    label_plural=_("Bat mitzvahs"),
    label_countable=ngettext("{count} bat mitzvah", "{count} bat mitzvahs"),
    after={Birth},
    before={Death},
    indicates=Birth,
)
class BatMitzvah(EventType):
    """
    .. plugin:: event-type:bat-mitzvah.
    """
