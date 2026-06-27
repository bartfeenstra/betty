"""
Julian calendars.
"""

from __future__ import annotations

from typing import final, override

from convertdate.julian import month_length, to_gregorian

from betty.calendar import to_year_zero
from betty.calendars._base import _CalendarBase
from betty.localizables.gettext import _
from betty.machine_name import MachineName


class _JulianCalendarBase(_CalendarBase):
    @final
    @override
    @classmethod
    def months(cls) -> int:
        return 12

    @final
    @override
    @classmethod
    def days(cls, year: int | None, month: int | None, /) -> int:
        if year is None or month is None:
            return 31
        return month_length(year, month)


@final
class Julian(_JulianCalendarBase):
    """
    The Julian calendar.
    """

    _id = MachineName("julian")
    _label = _("Julian")
    _public_label = _("Julian")
    _years = tuple(range(8, 9999))

    @override
    @classmethod
    def to_proleptic_iso8601(
        cls, year: int, month: int, day: int, /
    ) -> tuple[int, int, int]:
        return to_gregorian(year, month, day)


@final
class ProlepticJulian(_JulianCalendarBase):
    """
    The proleptic Julian calendar, classic, without year zero.
    """

    _id = MachineName("julian-proleptic")
    _label = _("Julian (proleptic)")
    _public_label = _("Julian")
    _years = (*range(-9999, -1), *range(1, 9999))

    @override
    @classmethod
    def to_proleptic_iso8601(
        cls, year: int, month: int, day: int, /
    ) -> tuple[int, int, int]:
        return to_gregorian(to_year_zero(year), month, day)
