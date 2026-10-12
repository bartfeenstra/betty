"""
The province place type.
"""

from __future__ import annotations

from typing import final

from betty.freezers.classtools import FrozenOnInit
from betty.localizables.gettext import _, ngettext
from betty.place_type import PlaceType, PlaceTypeDefinition


@final
@PlaceTypeDefinition(
    "province",
    label=_("Province"),
    label_plural=_("Provinces"),
    label_countable=ngettext("{count} province", "{count} provinces"),
)
class Province(PlaceType, FrozenOnInit):
    """
    .. plugin:: place-type:province.
    """
