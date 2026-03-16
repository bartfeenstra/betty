"""
The state place type.
"""

from __future__ import annotations

from typing import final

from betty.locale.localizable.gettext import _, ngettext
from betty.place_type import PlaceType, PlaceTypeDefinition


@final
@PlaceTypeDefinition(
    "state",
    label=_("State"),
    label_plural=_("States"),
    label_countable=ngettext("{count} state", "{count} states"),
)
class State(PlaceType):
    """
    .. plugin:: place-type:state.
    """
