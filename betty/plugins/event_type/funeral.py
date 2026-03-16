"""
The funeral event type.
"""

from __future__ import annotations

from typing import final

from betty.event_type import EventType, EventTypeDefinition
from betty.locale.localizable.gettext import _, ngettext
from betty.plugins.event_type.death import Death


@final
@EventTypeDefinition(
    "funeral",
    label=_("Funeral"),
    label_plural=_("Funerals"),
    label_countable=ngettext("{count} funeral", "{count} funerals"),
    after={Death},
    indicates=Death,
)
class Funeral(EventType):
    """
    .. plugin:: event-type:funeral.
    """
