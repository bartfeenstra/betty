"""
The building place type.
"""

from __future__ import annotations

from typing import final

from betty.locale.localizable.gettext import _, ngettext
from betty.place_type import PlaceType, PlaceTypeDefinition


@final
@PlaceTypeDefinition(
    "building",
    label=_("Building"),
    label_plural=_("Buildings"),
    label_countable=ngettext("{count} building", "{count} buildings"),
)
class Building(PlaceType):
    """
    .. plugin:: place-type:building.
    """
