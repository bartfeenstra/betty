"""
The farm place type.
"""

from __future__ import annotations

from typing import final

from betty.frosties.classtools import Frozen
from betty.localizables.gettext import _, ngettext
from betty.place_type import PlaceType, PlaceTypeDefinition


@final
@PlaceTypeDefinition(
    "farm",
    label=_("Farm"),
    label_plural=_("Farms"),
    label_countable=ngettext("{count} farm", "{count} farms"),
)
class Farm(PlaceType, Frozen):
    """
    .. plugin:: place-type:farm.
    """
