"""
The hamlet place type.
"""

from __future__ import annotations

from typing import final

from betty.localizables.gettext import _, ngettext
from betty.place_type import PlaceType, PlaceTypeDefinition


@final
@PlaceTypeDefinition(
    "hamlet",
    label=_("Hamlet"),
    label_plural=_("Hamlets"),
    label_countable=ngettext("{count} hamlet", "{count} hamlets"),
)
class Hamlet(PlaceType):
    """
    .. plugin:: place-type:hamlet.
    """
