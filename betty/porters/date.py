"""
Date porters.
"""

from __future__ import annotations

from typing import final, override

from betty.assertions.if_else import assert_if_else
from betty.date import AnyDate, Date, DateRange
from betty.portable import PortableData, Porter


@final
class AnyDatePorter(Porter[AnyDate]):
    """
    Port a date or date range.
    """

    load = override(
        assert_if_else(
            Date.data().porter.load,
            DateRange.data().porter.load,
        )
    )

    @override
    def dump(self, data: AnyDate, /) -> PortableData:
        return data.data().porter.dump(data)
