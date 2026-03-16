"""
The bat mitzvah event type.
"""

from __future__ import annotations

from typing import final

from betty.event_type import EventType, EventTypeDefinition
from betty.locale.localizable.gettext import _, ngettext
from betty.plugins.event_type.birth import Birth
from betty.plugins.event_type.death import Death


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
