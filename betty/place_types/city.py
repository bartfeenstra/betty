"""
The city place type.
"""

from __future__ import annotations

from typing import final

from betty.locale.localizable.gettext import _, ngettext
from betty.place_type import PlaceType, PlaceTypeDefinition


@final
@PlaceTypeDefinition(
    "city",
    label=_("City"),
    label_plural=_("Cities"),
    label_countable=ngettext("{count} city", "{count} cities"),
)
class City(PlaceType):
    """
    .. plugin:: place-type:city.
    """
