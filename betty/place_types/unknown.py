"""
The unknown place type.
"""

from __future__ import annotations

from typing import final

from betty.freezers.frozen import Frozen
from betty.localizables.gettext import _, ngettext
from betty.place_type import PlaceType, PlaceTypeDefinition


@final
@PlaceTypeDefinition(
    "unknown",
    label=_("Unknown"),
    label_plural=_("Unknowns"),
    label_countable=ngettext("{count} unknown", "{count} unknowns"),
)
class UnknownPlaceType(PlaceType, Frozen):
    """
    .. plugin:: place-type:unknown.
    """
