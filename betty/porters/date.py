"""
Date porters.
"""

from __future__ import annotations

from typing import final, override

from betty.date import AnyDate, Date, DateRange
from betty.portable import PortableData, Porter
from betty.validators.group import is_any


@final
class AnyDatePorter(Porter[AnyDate]):
    """
    Port a date or date range.
    """

    load = override(
        is_any(
            Date.definition.porter.load,
            DateRange.definition.porter.load,
        )
    )

    @override
    def dump(self, data: AnyDate, /) -> PortableData:
        return data.definition.porter.dump(data)
