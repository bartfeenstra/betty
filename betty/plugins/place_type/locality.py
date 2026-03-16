"""
The locality place type.
"""

from __future__ import annotations

from typing import final

from betty.locale.localizable.gettext import _, ngettext
from betty.place_type import PlaceType, PlaceTypeDefinition


@final
@PlaceTypeDefinition(
    "locality",
    label=_("Locality"),
    label_plural=_("Localities"),
    label_countable=ngettext("{count} locality", "{count} localities"),
)
class Locality(PlaceType):
    """
    .. plugin:: place-type:locality.
    """
