"""
Date data.
"""

from __future__ import annotations

from typing import final

from betty.data import DataDefinition
from betty.date import AnyDate, Date, DateRange
from betty.localizables.gettext import _
from betty.portable import PortableData, Porter
from betty.porters.date import AnyDatePorter


@final
class AnyDateDefinition(DataDefinition[AnyDate, Porter[AnyDate, PortableData]]):
    """
    The data definition for a date or a date range.
    """

    def __init__(self):
        super().__init__(
            label=_("Date"), porter=AnyDatePorter(), samples=[Date, DateRange]
        )
