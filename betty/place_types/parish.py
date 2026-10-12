"""
The parish place type.
"""

from __future__ import annotations

from typing import final

from betty.freezers.classtools import FrozenOnInit
from betty.localizables.gettext import _, ngettext
from betty.place_type import PlaceType, PlaceTypeDefinition


@final
@PlaceTypeDefinition(
    "parish",
    label=_("Parish"),
    label_plural=_("Parishes"),
    label_countable=ngettext("{count} parish", "{count} parishes"),
)
class Parish(PlaceType, FrozenOnInit):
    """
    .. plugin:: place-type:parish.
    """
