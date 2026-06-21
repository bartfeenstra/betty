"""
The cemetery place type.
"""

from __future__ import annotations

from typing import final

from betty.localizables.gettext import _, ngettext
from betty.place_type import PlaceType, PlaceTypeDefinition


@final
@PlaceTypeDefinition(
    "cemetery",
    label=_("Cemetery"),
    label_plural=_("Cemeteries"),
    label_countable=ngettext("{count} cemetery", "{count} cemeteries"),
)
class Cemetery(PlaceType):
    """
    .. plugin:: place-type:cemetery.
    """
