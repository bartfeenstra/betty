"""
The municipality place type.
"""

from __future__ import annotations

from typing import final

from betty.locale.localizable.gettext import _, ngettext
from betty.place_type import PlaceType, PlaceTypeDefinition


@final
@PlaceTypeDefinition(
    "municipality",
    label=_("Municipality"),
    label_plural=_("Municipalities"),
    label_countable=ngettext("{count} municipality", "{count} municipalities"),
)
class Municipality(PlaceType):
    """
    .. plugin:: place-type:municipality.
    """
