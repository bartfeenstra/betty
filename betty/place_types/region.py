"""
The region place type.
"""

from __future__ import annotations

from typing import final

from betty.freezers.classtools import FrozenOnInit
from betty.localizables.gettext import _, ngettext
from betty.place_type import PlaceType, PlaceTypeDefinition


@final
@PlaceTypeDefinition(
    "region",
    label=_("Region"),
    label_plural=_("Regions"),
    label_countable=ngettext("{count} region", "{count} regions"),
)
class Region(PlaceType, FrozenOnInit):
    """
    .. plugin:: place-type:region.
    """
