"""
Date data.
"""

from typing import final, override

from betty.assertion import assert_or
from betty.data import DataDefinition
from betty.date import AnyDate, Date, DateRange
from betty.locale.localizable.gettext import _
from betty.portable import PortableData, Porter


@final
class AnyDatePorter(Porter):
    """
    Port a date or date range.
    """

    @override
    def load(self, portable: PortableData, /) -> AnyDate:
        return assert_or(
            Date.data().porter.load,
            DateRange.data().porter.load,
        )(portable)

    @override
    def dump(self, data: AnyDate, /) -> PortableData:
        return data.data().porter.dump(data)


@final
class AnyDateDefinition(DataDefinition):
    """
    The data definition for a date or a date range.
    """

    def __init__(self):
        super().__init__(
            object, label=_("Date"), porter=AnyDatePorter(), samples=[Date, DateRange]
        )
