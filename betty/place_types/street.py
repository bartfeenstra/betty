"""
The street place type.
"""

from __future__ import annotations

from typing import final

from betty.localizables.gettext import _, ngettext
from betty.place_type import PlaceType, PlaceTypeDefinition


@final
@PlaceTypeDefinition(
    "street",
    label=_("Street"),
    label_plural=_("Streets"),
    label_countable=ngettext("{count} street", "{count} streets"),
)
class Street(PlaceType):
    """
    .. plugin:: place-type:street.
    """
