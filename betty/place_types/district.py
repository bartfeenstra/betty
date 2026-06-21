"""
The district place type.
"""

from __future__ import annotations

from typing import final

from betty.localizables.gettext import _, ngettext
from betty.place_type import PlaceType, PlaceTypeDefinition


@final
@PlaceTypeDefinition(
    "district",
    label=_("District"),
    label_plural=_("Districts"),
    label_countable=ngettext("{count} district", "{count} districts"),
)
class District(PlaceType):
    """
    .. plugin:: place-type:district.
    """
