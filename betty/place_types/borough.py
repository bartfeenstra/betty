"""
The borough place type.
"""

from __future__ import annotations

from typing import final

from betty.locale.localizable.gettext import _, ngettext
from betty.place_type import PlaceType, PlaceTypeDefinition


@final
@PlaceTypeDefinition(
    "borough",
    label=_("Borough"),
    label_plural=_("Boroughs"),
    label_countable=ngettext("{count} borough", "{count} boroughs"),
)
class Borough(PlaceType):
    """
    .. plugin:: place-type:borough.
    """
