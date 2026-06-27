"""
ISO 8601 calendars.
"""

from __future__ import annotations

from typing import final, override

from betty.calendars.gregorian import _GregorianCalendarBase
from betty.localizables.gettext import _
from betty.machine_name import MachineName


class _Iso8601CalendarBase(_GregorianCalendarBase):
    @final
    @override
    @classmethod
    def earliest(
        cls, year: int | None, month: int | None, day: int | None, /
    ) -> tuple[int | None, int | None, int | None]:
        return (
            cls.years()[0] if year is None else year,
            1 if month is None else month,
            1 if day is None else month,
        )

    @final
    @override
    @classmethod
    def latest(
        cls, year: int | None, month: int | None, day: int | None, /
    ) -> tuple[int | None, int | None, int | None]:
        if year is None:
            year = cls.years()[-1]
        if month is None:
            month = 12
        if day is None:
            day = cls.days(year, month)
        return (year, month, day)


@final
class Iso8601(_Iso8601CalendarBase):
    """
    The ISO 8601 calendar.
    """

    _id = MachineName("iso8601")
    _label = _("ISO 8601")
    _public_label = _label
    _years = tuple(range(9999))

    @override
    @classmethod
    def to_proleptic_iso8601(
        cls, year: int, month: int, day: int, /
    ) -> tuple[int, int, int]:
        return year, month, day


@final
class ProlepticIso8601(_Iso8601CalendarBase):
    """
    The proleptic ISO 8601 calendar, with year zero.
    """

    _id = MachineName("iso8601-proleptic")
    _label = _("ISO 8601 (proleptic)")
    _public_label = _("ISO 8601")
    _years = tuple(range(-9999, 9999))

    @override
    @classmethod
    def to_proleptic_iso8601(
        cls, year: int, month: int, day: int, /
    ) -> tuple[int, int, int]:
        return year, month, day
