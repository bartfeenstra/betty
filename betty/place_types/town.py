"""
The town place type.
"""

from __future__ import annotations

from typing import final

from betty.frosties.classtools import Frozen
from betty.localizables.gettext import _, ngettext
from betty.place_type import PlaceType, PlaceTypeDefinition


@final
@PlaceTypeDefinition(
    "town",
    label=_("Town"),
    label_plural=_("Towns"),
    label_countable=ngettext("{count} town", "{count} towns"),
)
class Town(PlaceType, Frozen):
    """
    .. plugin:: place-type:town.
    """
