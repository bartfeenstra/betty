"""
Localize dates.
"""

from __future__ import annotations

import calendar
import datetime
import operator
from contextlib import suppress
from functools import total_ordering
from typing import TYPE_CHECKING, Any, final, override

from babel import dates

from betty.data import Data
from betty.datas.aggregate.record.object import ObjectDefinition
from betty.datas.bool import BoolDefinition
from betty.datas.int import IntDefinition
from betty.locale.localizable import Localizable
from betty.locale.localizable.gettext import _
from betty.property import Optional, Property
from betty.sample import Sample, Size

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping
    from types import NotImplementedType

    from betty.locale import Localized
    from betty.locale.localize import Localizer
    from betty.typing import Intersection


@final
class IncompleteDateError(ValueError):
    """
    Raised when a date-like was unexpectedly incomplete.
    """


_LOCALIZE_DATE_PART_FORMATS: Mapping[tuple[bool, bool, bool], Localizable] = {
    (True, True, True): _("MMMM d, y"),
    (True, True, False): _("MMMM, y"),
    (True, False, False): _("y"),
    (False, True, True): _("MMMM d"),
    (False, True, False): _("MMMM"),
}


def _localize_date_parts(localizer: Localizer, date: Date | None, /) -> str:
    if date is None:
        raise IncompleteDateError("This date is None.")
    try:
        date_parts_format = _LOCALIZE_DATE_PART_FORMATS[
            (date.year is not None, date.month is not None, date.day is not None)
        ].localize(localizer)
    except KeyError:
        raise IncompleteDateError(
            "This date does not have enough parts to be rendered."
        ) from None
    parts = (1 if x is None else x for x in date.parts)
    return dates.format_date(datetime.date(*parts), date_parts_format, localizer.locale)


@final
@ObjectDefinition(
    label=_("Date"),
    samples=[
        lambda: Sample(Date(), label="Minimal", size=Size.MINIMAL),
        lambda: Sample(Date(1970, 1, 1, fuzzy=True), label="Full", size=Size.FULL),
    ],
)
class Date(Localizable, Data):
    """
    A (Gregorian) date.
    """

    _LOCALIZE_FORMATS: Mapping[tuple[bool | None], Localizable] = {
        (True,): _("around {date}"),
        (False,): _("{date}"),
    }

    year = Optional(Property(IntDefinition(label=_("Year"))))
    month = Optional(Property(IntDefinition(label=_("Month"))))
    day = Optional(Property(IntDefinition(label=_("Day"))))
    fuzzy = Property(
        BoolDefinition(label=_("Fuzzy")),
        omit_load=True,
        omit_dump=lambda data: data is False,
    )

    def __init__(
        self,
        year: int | None = None,
        month: int | None = None,
        day: int | None = None,
        *,
        fuzzy: bool = False,
    ):
        self.year = year
        self.month = month
        self.day = day
        self.fuzzy = fuzzy

    @override
    def localize(self, localizer: Localizer, /) -> Intersection[Localized, str]:
        try:
            return (
                self
                ._LOCALIZE_FORMATS[(self.fuzzy,)]
                .format(
                    date=_localize_date_parts(localizer, self),
                )
                .localize(localizer)
            )
        except IncompleteDateError:
            return _("unknown date").localize(localizer)

    @property
    def comparable(self) -> bool:
        """
        If this date is comparable to other date-likes.
        """
        return self.year is not None

    @property
    def complete(self) -> bool:
        """
        Whether this date is complete.
        """
        return self.year is not None and self.month is not None and self.day is not None

    @property
    def parts(self) -> tuple[int | None, int | None, int | None]:
        """
        The date parts: a 3-tuple of the year, month, and day.
        """
        return self.year, self.month, self.day

    def to_range(self) -> DateRange:
        """
        Convert this date to a date range.
        """
        if not self.comparable:
            raise ValueError(
                f"Cannot convert non-comparable date {self!r} to a date range."
            )
        assert self.year is not None
        if self.month is None:
            month_start = 1
            month_end = 12
        else:
            month_start = month_end = self.month
        if self.day is None:
            day_start = 1
            day_end = calendar.monthrange(self.year, month_end)[1]
        else:
            day_start = day_end = self.day
        return DateRange(
            Date(self.year, month_start, day_start), Date(self.year, month_end, day_end)
        )

    def _compare(
        self, other: Any, comparator: Callable[[Any, Any], bool], /
    ) -> bool | NotImplementedType:
        if not isinstance(other, Date):
            return NotImplemented
        selfish = self
        if not selfish.comparable or not other.comparable:
            return NotImplemented
        if selfish.complete and other.complete:
            return comparator(selfish.parts, other.parts)
        if not other.complete:
            other = other.to_range()
        if not selfish.complete:
            selfish = selfish.to_range()
        return comparator(selfish, other)

    def __contains__(self, other: AnyDate) -> bool:
        if isinstance(other, Date):
            return self == other
        return self in other

    def __lt__(self, other: Any) -> bool:
        return self._compare(other, operator.lt)

    def __le__(self, other: Any) -> bool:
        return self._compare(other, operator.le)

    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Date):
            return NotImplemented
        return self.parts == other.parts

    def __ge__(self, other: Any) -> bool:
        return self._compare(other, operator.ge)

    def __gt__(self, other: Any) -> bool:
        return self._compare(other, operator.gt)

    @classmethod
    def _load_date(cls, value: str) -> tuple[int | None, int | None, int | None]:
        raise NotImplementedError


def _dump_date_iso8601(date: Date, /) -> str | None:
    if not date.complete:
        return None
    assert date.year
    assert date.month
    assert date.day
    return f"{date.year:04d}-{date.month:02d}-{date.day:02d}"


@final
@total_ordering
@ObjectDefinition(label=_("Date range"))
class DateRange(Localizable, Data):
    """
    A date range can describe a period of time between, before, after, or around start and/or end dates.
    """

    _LOCALIZE_FORMATS: Mapping[
        tuple[bool | None, bool | None, bool | None, bool | None], Localizable
    ] = {
        (False, False, False, False): _("from {start_date} until {end_date}"),
        (False, False, False, True): _(
            "from {start_date} until sometime before {end_date}"
        ),
        (False, False, True, False): _("from {start_date} until around {end_date}"),
        (False, False, True, True): _(
            "from {start_date} until sometime before around {end_date}"
        ),
        (False, True, False, False): _(
            "from sometime after {start_date} until {end_date}"
        ),
        (False, True, False, True): _("sometime between {start_date} and {end_date}"),
        (False, True, True, False): _(
            "from sometime after {start_date} until around {end_date}"
        ),
        (False, True, True, True): _(
            "sometime between {start_date} and around {end_date}"
        ),
        (True, False, False, False): _("from around {start_date} until {end_date}"),
        (True, False, False, True): _(
            "from around {start_date} until sometime before {end_date}"
        ),
        (True, False, True, False): _(
            "from around {start_date} until around {end_date}"
        ),
        (True, False, True, True): _(
            "from around {start_date} until sometime before around {end_date}"
        ),
        (True, True, False, False): _(
            "from sometime after around {start_date} until {end_date}"
        ),
        (True, True, False, True): _(
            "sometime between around {start_date} and {end_date}"
        ),
        (True, True, True, False): _(
            "from sometime after around {start_date} until around {end_date}"
        ),
        (True, True, True, True): _(
            "sometime between around {start_date} and around {end_date}"
        ),
        (False, False, None, None): _("from {start_date}"),
        (False, True, None, None): _("sometime after {start_date}"),
        (True, False, None, None): _("from around {start_date}"),
        (True, True, None, None): _("sometime after around {start_date}"),
        (None, None, False, False): _("until {end_date}"),
        (None, None, False, True): _("sometime before {end_date}"),
        (None, None, True, False): _("until around {end_date}"),
        (None, None, True, True): _("sometime before around {end_date}"),
    }

    start = Optional(Property(Date))
    start_is_boundary = Property(
        BoolDefinition(label=_("Start date is a boundary")),
        omit_load=True,
        omit_dump=lambda data: data is False,
    )
    end = Optional(Property(Date))
    end_is_boundary = Property(
        BoolDefinition(label=_("End date is a boundary")),
        omit_load=True,
        omit_dump=lambda data: data is False,
    )

    def __init__(
        self,
        start: Date | None = None,
        end: Date | None = None,
        *,
        start_is_boundary: bool = False,
        end_is_boundary: bool = False,
    ):
        self.start = start
        self.start_is_boundary = start_is_boundary
        self.end = end
        self.end_is_boundary = end_is_boundary

    @override
    def localize(self, localizer: Localizer, /) -> Intersection[Localized, str]:
        formatter_configuration: tuple[
            bool | None, bool | None, bool | None, bool | None
        ] = (None, None, None, None)
        formatter_arguments = {}

        with suppress(IncompleteDateError):
            formatter_arguments["start_date"] = _localize_date_parts(
                localizer, self.start
            )
            formatter_configuration = (
                None if self.start is None else self.start.fuzzy,
                self.start_is_boundary,
                formatter_configuration[2],
                formatter_configuration[3],
            )

        with suppress(IncompleteDateError):
            formatter_arguments["end_date"] = _localize_date_parts(localizer, self.end)
            formatter_configuration = (
                formatter_configuration[0],
                formatter_configuration[1],
                None if self.end is None else self.end.fuzzy,
                self.end_is_boundary,
            )

        if not formatter_arguments:
            raise IncompleteDateError(
                "This date range does not have enough parts to be rendered."
            )

        return (
            self
            ._LOCALIZE_FORMATS[formatter_configuration]
            .format(**formatter_arguments)
            .localize(localizer)
        )

    @property
    def comparable(self) -> bool:
        """
        If this date is comparable to other date-likes.
        """
        return (
            self.start is not None
            and self.start.comparable
            or self.end is not None
            and self.end.comparable
        )

    def __contains__(self, other: AnyDate) -> bool:
        if not self.comparable:
            return False

        if isinstance(other, Date):
            others = [other]
        else:
            if not other.comparable:
                return False
            others = []
            if other.start is not None and other.start.comparable:
                others.append(other.start)
            if other.end is not None and other.end.comparable:
                others.append(other.end)

        if self.start is not None and self.end is not None:
            if isinstance(other, DateRange) and (
                other.start is None or other.end is None
            ):
                if other.start is None:
                    return self.start <= other.end or self.end <= other.end
                if other.end is None:
                    return self.start >= other.start or self.end >= other.start
            for another in others:
                if self.start <= another <= self.end:
                    return True
            if isinstance(other, DateRange):
                for selfdate in [self.start, self.end]:
                    if other.start <= selfdate <= other.end:
                        return True

        elif self.start is not None:
            # Two date ranges with start dates only always overlap.
            if isinstance(other, DateRange) and other.end is None:
                return True

            for another in others:
                if self.start <= another:
                    return True
        elif self.end is not None:
            # Two date ranges with end dates only always overlap.
            if isinstance(other, DateRange) and other.start is None:
                return True

            for another in others:
                if another <= self.end:
                    return True
        return False

    def _get_comparable_date(self, date: Date | None, /) -> Date | None:
        if date and date.comparable:
            return date
        return None

    def __lt__(self, other: Any) -> bool:
        if not isinstance(other, Date | DateRange):
            return NotImplemented

        self_start = self._get_comparable_date(self.start)
        self_end = self._get_comparable_date(self.end)
        if isinstance(other, DateRange):
            other_start = self._get_comparable_date(other.start)
            other_end = self._get_comparable_date(other.end)
            if self_start is None:
                if self_end is None:
                    return NotImplemented
                if other_start is None:
                    if other_end is None:
                        return NotImplemented
                    return self_end < other_end
                if other_end is None:
                    return self_end <= other_start
                return self_end <= other_start
            if self_end is None:
                if other_start is None:
                    if other_end is None:
                        return NotImplemented
                    return self_start < other_end
                if other_end is None:
                    return self_start < other_start
                return self_start < other_start
            if other_start is None:
                if other_end is None:
                    return NotImplemented
                return self_start < other_end or self_end <= other_end
            if other_end is None:
                return self_start <= other_start
            return self_start < other_start
        if self_start is None:
            if self_end is None:
                return NotImplemented
            return self_end <= other
        if self_end is None:
            return self_start < other
        return self_start < other

    @override
    def __eq__(self, other: object) -> bool:
        if isinstance(other, Date):
            return False

        if not isinstance(other, DateRange):
            return NotImplemented
        return (self.start, self.end, self.start_is_boundary, self.end_is_boundary) == (
            other.start,
            other.end,
            other.start_is_boundary,
            other.end_is_boundary,
        )


type AnyDate = Date | DateRange
