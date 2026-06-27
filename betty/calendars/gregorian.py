"""
Gregorian calendars.
"""

from __future__ import annotations

from typing import final, override

from convertdate.gregorian import monthrange

from betty.calendar import to_year_zero
from betty.calendars._base import _CalendarBase
from betty.localizables.gettext import _
from betty.machine_name import MachineName


class _GregorianCalendarBase(_CalendarBase):
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
        return monthrange(year, month)[1]


@final
class Gregorian(_GregorianCalendarBase):
    """
    The Gregorian calendar.
    """

    _id = MachineName("gregorian")
    _label = _("Gregorian")
    _public_label = _label
    _years = tuple(range(1582, 9999))

    @override
    @classmethod
    def to_proleptic_iso8601(
        cls, year: int, month: int, day: int, /
    ) -> tuple[int, int, int]:
        return year, month, day


@final
class ProlepticGregorian(_GregorianCalendarBase):
    """
    The proleptic Gregorian calendar, classic, without year zero.
    """

    _id = MachineName("gregorian-proleptic")
    _label = _("Gregorian (proleptic)")
    _public_label = _("Gregorian")
    _years = (*range(-9999, -1), *range(1, 9999))

    @override
    @classmethod
    def to_proleptic_iso8601(
        cls, year: int, month: int, day: int, /
    ) -> tuple[int, int, int]:
        return to_year_zero(year), month, day
