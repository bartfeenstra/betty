"""
The number place type.
"""

from __future__ import annotations

from typing import final

from betty.locale.localizable.gettext import _, ngettext
from betty.place_type import PlaceType, PlaceTypeDefinition


@final
@PlaceTypeDefinition(
    "number",
    label=_("Number"),
    label_plural=_("Numbers"),
    label_countable=ngettext("{count} number", "{count} numbers"),
    description=_("A place number, such as a house or flat number."),
)
class Number(PlaceType):
    """
    .. plugin:: place-type:number.
    """
