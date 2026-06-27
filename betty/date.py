"""
The date API.
"""

from __future__ import annotations

import datetime
from abc import ABC, abstractmethod
from operator import not_
from typing import TYPE_CHECKING, Any, Final, Self, TypeGuard, final, overload, override

from babel import dates

from betty import calendars
from betty.calendars import ProlepticIso8601
from betty.data import Data, DataDefinition
from betty.datas.aggregate.record import FieldDefinition
from betty.datas.aggregate.record.object import ObjectDefinition
from betty.datas.bool import BoolDefinition
from betty.datas.int import IntDefinition
from betty.datas.optional import OptionalDefinition
from betty.exception import HumanFacingException
from betty.localizable import Localizable
from betty.localizables.gettext import _, pgettext
from betty.localized import LocalizedStr
from betty.machine_name import MachineName
from betty.porters.callback import CallbackPorter
from betty.porters.omit_field import OmitFieldPorter
from betty.sample import Sample, Size

if TYPE_CHECKING:
    from collections.abc import Mapping

    from betty.calendar import Calendar
    from betty.localizer import Localizer


type DateParts = (
    tuple[int, int | None, int | None]
    | tuple[int | None, int, int | None]
    | tuple[int | None, int | None, int]
)


def validate_date_parts(
    parts: tuple[int | None, int | None, int | None], /
) -> TypeGuard[DateParts]:
    """
    Validate date parts to ensue they are not all empty.
    """
    return parts != (None, None, None)


@final
class InvalidDate(HumanFacingException, ValueError):
    """
    Raised when a date is invalid.
    """

    def __init__(
        self,
        year: int | None,
        month: int | None,
        day: int | None,
        calendar: type[Calendar],
        /,
    ):
        super().__init__(
            _("Invalid date {year}-{month}-{day} on the {calendar} calendar.").format(
                year="...." if year is None else str(year),
                month=".." if month is None else str(month),
                day=".." if day is None else str(day),
                calendar=calendar.label(),
            )
        )


class DateExpression(Localizable, Data[ObjectDefinition], ABC):
    """
    A date-like expression.
    """

    @final
    def __init_subclass__(cls, **kwargs: Any):
        assert cls.__module__ == "betty.date", (
            "Third-party date expressions are not supported."
        )
        super().__init_subclass__(**kwargs)

    @final
    def __truediv__[OtherT: DateExpression](self, other: OtherT) -> Self | OtherT:
        """
        Return the earliest of the two date expressions, or return the left operand if no comparison was possible.

        This operation may be lossy.
        """
        return self if self <= other else other

    @final
    def __mul__[OtherT: DateExpression](self, other: OtherT) -> Self | OtherT:
        """
        Return the latest of the two date expressions, or return the left operand if no comparison was possible.

        This operation may be lossy.
        """
        return self if self >= other else other

    @abstractmethod
    def __contains__(self, other: DateExpression) -> bool:
        pass


@final
@ObjectDefinition(
    label=_("Date"),
    fields={
        "year": FieldDefinition(
            OptionalDefinition(IntDefinition(label=_("Year"))),
            optional=True,
            porter=OmitFieldPorter.new(lambda data: data is None),
        ),
        "month": FieldDefinition(
            OptionalDefinition(IntDefinition(label=_("Month"))),
            optional=True,
            porter=OmitFieldPorter.new(lambda data: data is None),
        ),
        "day": FieldDefinition(
            OptionalDefinition(IntDefinition(label=_("Day"))),
            optional=True,
            porter=OmitFieldPorter.new(lambda data: data is None),
        ),
        "calendar": FieldDefinition(
            DataDefinition(
                label=_("Calendar"),
                porter=CallbackPorter(
                    lambda data: calendars.get(MachineName.data().porter.load(data)),
                    lambda data: MachineName.data().porter.dump(data.id()),
                ),
            ),
            optional=True,
            porter=OmitFieldPorter.new(lambda data: data is ProlepticIso8601),
        ),
        "imprecise": FieldDefinition(
            BoolDefinition(label=_("Imprecise")),
            optional=True,
            porter=OmitFieldPorter.new(not_),
        ),
    },
    factory=lambda *, year, month, day, imprecise: Date(
        year, month, day, imprecise=imprecise
    ),
    samples=[
        lambda: Sample(Date(1), label="Minimal", size=Size.MINIMAL),
        lambda: Sample(Date(1970, 1, 1, imprecise=True), label="Full", size=Size.FULL),
    ],
)
class Date(DateExpression):
    """
    A single date.
    """

    __slots__ = (
        "calendar",
        "year",
        "month",
        "day",
        "imprecise",
    )

    _format_date_patterns: Final[dict[tuple[bool, bool, bool], Localizable]] = {
        (True, True, True): pgettext("date", "MMMM d, y"),
        (True, True, False): pgettext("date", "MMMM, y"),
        (True, False, True): pgettext("date", "'day' d 'of the month,' y"),
        (True, False, False): pgettext("date", "y"),
        (False, True, True): pgettext("date", "MMMM d"),
        (False, True, False): pgettext("date", "MMMM"),
        (False, False, True): pgettext("date", "'day' d 'of the month'"),
    }

    @overload
    def __init__(
        self,
        year: int,
        month: int | None = None,
        day: int | None = None,
        /,
        *,
        calendar: type[Calendar] = ProlepticIso8601,
        imprecise: bool = False,
    ):
        pass

    @overload
    def __init__(
        self,
        year: int | None,
        month: int,
        day: int | None = None,
        /,
        *,
        calendar: type[Calendar] = ProlepticIso8601,
        imprecise: bool = False,
    ):
        pass

    @overload
    def __init__(
        self,
        year: int | None,
        month: int | None,
        day: int,
        /,
        *,
        calendar: type[Calendar] = ProlepticIso8601,
        imprecise: bool = False,
    ):
        pass

    def __init__(
        self,
        year,
        month=None,
        day=None,
        /,
        *,
        calendar=ProlepticIso8601,
        imprecise=False,
    ):
        if calendar.validate(year, month, day) is False:
            raise InvalidDate(year, month, day, calendar)
        super().__init__()
        self.calendar: Final[type[Calendar]] = calendar
        """
        The calendar on which the date is expressed.
        """

        self.year: Final[int | None] = year
        """
        The year.
        """

        self.month: Final[int | None] = month
        """
        The month.
        """

        self.day: Final[int | None] = day
        """
        The day.
        """

        self.imprecise: Final[bool] = imprecise
        """
        Whether the year, month, and/or day are imprecise, e.g. not exactly known. 
        """

        # @todo Can we skip some calculations for complete dates?
        self._earliest = calendar.earliest(year, month, day)
        self._latest = calendar.latest(year, month, day)
        self._earliest_proleptic_iso8601 = (
            self._earliest
            if calendar is ProlepticIso8601
            else calendar.to_proleptic_iso8601(*self._earliest)
        )
        self._latest_proleptic_iso8601 = (
            self._latest
            if calendar is ProlepticIso8601
            else calendar.to_proleptic_iso8601(*self._latest)
        )

    def __hash__(self):
        return hash((type(self), self.year, self.month, self.day, self.imprecise))

    def __lt__(self, other: Any) -> bool:
        if not isinstance(other, Date):
            return NotImplemented
        # @todo Date parts can be None...
        if self.calendar is other.calendar:
            return self._latest < other._earliest
        return self._latest_proleptic_iso8601 < other._earliest_proleptic_iso8601

    def __le__(self, other: Any) -> bool:
        return self < other or self == other

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Date):
            return NotImplemented
        return (self.year, self.month, self.day, self.imprecise) == (
            other.year,
            other.month,
            other.day,
            other.imprecise,
        )

    def __ge__(self, other: Any) -> bool:
        return self > other or self == other

    def __gt__(self, other: Any) -> bool:
        if not isinstance(other, Date):
            return NotImplemented
        raise NotImplementedError

    def __contains__(self, other: Any) -> bool:
        if not isinstance(other, Date):
            return False
        return self == other

    def __repr__(self):
        return f"<Date: year={self.year}, month={self.month}, day={self.day}, imprecise={self.imprecise}, calendar={self.calendar.id()}>"

    @override
    def localize(self, localizer: Localizer, /) -> LocalizedStr:
        pattern = self._format_date_patterns[
            (self.year is not None, self.month is not None, self.day is not None)
        ].localize(localizer)
        localized = LocalizedStr(
            dates.format_date(
                datetime.date(
                    1 if self.year is None else self.year,
                    1 if self.month is None else self.month,
                    1 if self.day is None else self.day,
                ),
                pattern,
                pattern.locale,
            ),
            locale=pattern.locale,
        )
        if self.imprecise:
            localized = _("around {date}").format(date=localized).localize(localizer)
        if self.calendar is not ProlepticIso8601:
            localized = (
                _("{date} ({calendar})")
                .format(date=localized, calendar=self.calendar.public_label())
                .localize(localizer)
            )
        return localized


@final
@ObjectDefinition(
    label=_("Date range"),
    fields={
        "start": FieldDefinition(
            OptionalDefinition(Date),
            label=_("Start date"),
            optional=True,
            porter=OmitFieldPorter.new(lambda data: data is None),
        ),
        "start_is_boundary": FieldDefinition(
            BoolDefinition(label=_("Start date is a boundary")),
            optional=True,
            porter=OmitFieldPorter.new(not_),
        ),
        "end": FieldDefinition(
            OptionalDefinition(Date),
            label=_("End date"),
            optional=True,
            porter=OmitFieldPorter.new(lambda data: data is None),
        ),
        "end_is_boundary": FieldDefinition(
            BoolDefinition(label=_("End date is a boundary")),
            optional=True,
            porter=OmitFieldPorter.new(not_),
        ),
    },
    factory=lambda *, start, end, start_is_boundary, end_is_boundary: DateRange(
        start, end, start_is_boundary=start_is_boundary, end_is_boundary=end_is_boundary
    ),
    samples=[
        lambda: Sample(
            DateRange(Date.data().samples.get(Size.MINIMAL).subject),
            label="Minimal",
            size=Size.MINIMAL,
        ),
        lambda: Sample(
            DateRange(None, Date.data().samples.get(Size.MINIMAL).subject),
            label="Minimal",
            size=Size.MINIMAL,
        ),
        lambda: Sample(
            DateRange(
                Date.data().samples.get(Size.FULL).subject,
                DateRange.data().samples.get(Size.FULL).subject,
            ),
            label="Full",
            size=Size.FULL,
        ),
    ],
)
class DateRange(DateExpression):
    """
    A date range can describe a period of time between, before, after, or around start and/or end dates.
    """

    __slots__ = ("start", "start_is_boundary", "end", "end_is_boundary")

    _localizables: Final[Mapping[tuple[bool | None, bool | None], Localizable]] = {
        (False, False): _("from {start_date} until {end_date}"),
        (False, True): _("from {start_date} until sometime before {end_date}"),
        (True, False): _("from sometime after {start_date} until {end_date}"),
        (True, True): _("sometime between {start_date} and {end_date}"),
        (False, None): _("from {start_date}"),
        (True, None): _("sometime after {start_date}"),
        (None, False): _("until {end_date}"),
        (None, True): _("sometime before {end_date}"),
    }

    @overload
    def __init__(
        self,
        start: Date,
        end: Date,
        /,
        *,
        start_is_boundary: bool = False,
        end_is_boundary: bool = False,
    ):
        pass

    @overload
    def __init__(
        self,
        start: Date | None,
        end: Date,
        /,
        *,
        start_is_boundary: bool = False,
        end_is_boundary: bool = False,
    ):
        pass

    @overload
    def __init__(
        self,
        start: Date,
        end: Date | None = None,
        /,
        *,
        start_is_boundary: bool = False,
        end_is_boundary: bool = False,
    ):
        pass

    def __init__(
        self, start, end=None, /, *, start_is_boundary=False, end_is_boundary=False
    ):
        super().__init__()
        self.start: Final[Date | None] = start
        self.start_is_boundary: Final[bool] = start_is_boundary
        self.end: Final[Date | None] = end
        self.end_is_boundary: Final[bool] = end_is_boundary

    def __hash__(self):
        return hash((
            type(self),
            self.start,
            self.end,
            self.start_is_boundary,
            self.end_is_boundary,
        ))

    @override
    def __contains__(self, other: DateExpression) -> bool:
        raise NotImplementedError

    def __repr__(self):
        return f"<DateRange: start={repr(self.start)}, start_is_boundary={self.start_is_boundary}, end={repr(self.end)}, end_is_boundary={self.end_is_boundary}>"

    @override
    def localize(self, localizer: Localizer, /) -> LocalizedStr:
        localizable_key: tuple[bool | None, bool | None] = (None, None)
        localizable_args = {}

        if self.start:
            localizable_args["start_date"] = self.start.localize(localizer)
            localizable_key = (
                self.start_is_boundary,
                localizable_key[1],
            )

        if self.end:
            localizable_args["end_date"] = self.end.localize(localizer)
            localizable_key = (
                localizable_key[0],
                self.end_is_boundary,
            )

        return (
            self
            ._localizables[localizable_key]
            .format(**localizable_args)
            .localize(localizer)
        )
