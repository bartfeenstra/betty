"""
The neighborhood place type.
"""

from __future__ import annotations

from typing import final

from betty.localizables.gettext import _, ngettext
from betty.place_type import PlaceType, PlaceTypeDefinition


@final
@PlaceTypeDefinition(
    "neighborhood",
    label=_("Neighborhood"),
    label_plural=_("Neighborhoods"),
    label_countable=ngettext("{count} neighborhood", "{count} neighborhoods"),
)
class Neighborhood(PlaceType):
    """
    .. plugin:: place-type:neighborhood.
    """
