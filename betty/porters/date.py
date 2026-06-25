"""
Date porters.
"""

from __future__ import annotations

from typing import final, override

from betty.assertions.if_else import assert_if_else
from betty.date import AnyDate, Date, DateRange
from betty.portable import PortableData, Porter


@final
class AnyDatePorter(Porter[AnyDate, PortableData]):
    """
    Port a date or date range.
    """

    @override
    def load(self, portable: PortableData, /) -> AnyDate:
        return assert_if_else(
            Date.data().porter.load,
            DateRange.data().porter.load,
        )(portable)

    @override
    def dump(self, data: AnyDate, /) -> PortableData:
        return data.data().porter.dump(data)
