"""
The country place type.
"""

from __future__ import annotations

from typing import final

from betty.localizables.gettext import _, ngettext
from betty.place_type import PlaceType, PlaceTypeDefinition


@final
@PlaceTypeDefinition(
    "country",
    label=_("Country"),
    label_plural=_("Countries"),
    label_countable=ngettext("{count} country", "{count} countries"),
)
class Country(PlaceType):
    """
    .. plugin:: place-type:country.
    """
