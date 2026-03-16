"""
The county place type.
"""

from __future__ import annotations

from typing import final

from betty.locale.localizable.gettext import _, ngettext
from betty.place_type import PlaceType, PlaceTypeDefinition


@final
@PlaceTypeDefinition(
    "county",
    label=_("County"),
    label_plural=_("Counties"),
    label_countable=ngettext("{count} county", "{count} counties"),
)
class County(PlaceType):
    """
    .. plugin:: place-type:county.
    """
