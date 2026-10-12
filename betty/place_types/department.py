"""
The department place type.
"""

from __future__ import annotations

from typing import final

from betty.freezers.classtools import FrozenOnInit
from betty.localizables.gettext import _, ngettext
from betty.place_type import PlaceType, PlaceTypeDefinition


@final
@PlaceTypeDefinition(
    "department",
    label=_("Department"),
    label_plural=_("Departments"),
    label_countable=ngettext("{count} department", "{count} departments"),
)
class Department(PlaceType, FrozenOnInit):
    """
    .. plugin:: place-type:department.
    """
