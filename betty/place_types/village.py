"""
The village place type.
"""

from __future__ import annotations

from typing import final

from betty.localizables.gettext import _, ngettext
from betty.place_type import PlaceType, PlaceTypeDefinition


@final
@PlaceTypeDefinition(
    "village",
    label=_("Village"),
    label_plural=_("Villages"),
    label_countable=ngettext("{count} village", "{count} villages"),
)
class Village(PlaceType):
    """
    .. plugin:: place-type:village.
    """
