"""
Localize dates.
"""

from __future__ import annotations

import calendar
import operator
from collections.abc import Callable, Mapping
from functools import total_ordering
from typing import TYPE_CHECKING, Any, TypeAlias, final

from typing_extensions import override

from betty.classtools import Singleton
from betty.json.linked_data import (
    JsonLdObject,
    LinkedDataDumpableWithSchemaJsonLdObject,
    dump_context,
)
from betty.json.schema import Boolean, Null, Number, OneOf, String

if TYPE_CHECKING:
    from types import NotImplementedType

    from betty.project import Project
    from betty.serde.dump import Dump, DumpMapping


class IncompleteDateError(ValueError):
    """
    Raised when a date-like was unexpectedly incomplete.
    """


@final
class DateSchema(Singleton, JsonLdObject):
    """
    A JSON Schema for :py:type:`betty.date.Date`.
    """

    def __init__(self):
        super().__init__(def_name="date", title="Date")
        self.add_property("fuzzy", Boolean(title="Fuzzy"))
        self.add_property("year", Number(title="Year"), False)
        self.add_property("month", Number(title="Month"), False)
        self.add_property("day", Number(title="Day"), False)
        self.add_property(
            "iso8601",
            String(
                pattern="^\\d\\d\\d\\d-\\d\\d-\\d\\d$", description="An ISO 8601 date."
            ),
            False,
        )


class Date(LinkedDataDumpableWithSchemaJsonLdObject):
    """
    A (Gregorian) date.
    """

    year: int | None
    month: int | None
    day: int | None
    fuzzy: bool

    def __init__(
        self,
        year: int | None = None,
        month: int | None = None,
        day: int | None = None,
        fuzzy: bool = False,
    ):
        self.year = year
        self.month = month
        self.day = day
        self.fuzzy = fuzzy

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
                f"Cannot convert non-comparable date {self} to a date range."
            )
        if self.month is None:
            month_start = 1
            month_end = 12
        else:
            month_start = month_end = self.month
        if self.day is None:
            day_start = 1
            day_end = calendar.monthrange(
                self.year,  # type: ignore[arg-type]
                month_end,
            )[1]
        else:
            day_start = day_end = self.day
        return DateRange(
            Date(self.year, month_start, day_start), Date(self.year, month_end, day_end)
        )

    def _compare(
        self, other: Any, comparator: Callable[[Any, Any], bool]
    ) -> bool | NotImplementedType:
        if not isinstance(other, Date):
            return NotImplemented  # type: ignore[no-any-return]
        selfish = self
        if not selfish.comparable or not other.comparable:
            return NotImplemented  # type: ignore[no-any-return]
        if selfish.complete and other.complete:
            return comparator(selfish.parts, other.parts)
        if not other.complete:
            other = other.to_range()
        if not selfish.complete:
            selfish = selfish.to_range()  # type: ignore[assignment]
        return comparator(selfish, other)

    def __contains__(self, other: DateLike) -> bool:
        if isinstance(other, Date):
            return self == other
        return self in other

    def __lt__(self, other: Any) -> bool:
        return self._compare(other, operator.lt)

    def __le__(self, other: Any) -> bool:
        return self._compare(other, operator.le)

    @override
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Date):
            return NotImplemented
        return self.parts == other.parts

    def __ge__(self, other: Any) -> bool:
        return self._compare(other, operator.ge)

    def __gt__(self, other: Any) -> bool:
        return self._compare(other, operator.gt)

    @override
    async def dump_linked_data(
        self,
        project: Project,
        context_definition: str | None = None,
    ) -> DumpMapping[Dump]:
        dump = await super().dump_linked_data(project)
        dump["fuzzy"] = self.fuzzy
        if self.year:
            dump["year"] = self.year
        if self.month:
            dump["month"] = self.month
        if self.day:
            dump["day"] = self.day
        if self.comparable:
            dump["iso8601"] = _dump_date_iso8601(self)
            # Set a single term definition because JSON-LD does not let us apply multiple
            # for the same term (key).
            if context_definition:
                dump_context(dump, iso8601=context_definition)
        return dump

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project) -> DateSchema:
        return DateSchema()


def _dump_date_iso8601(date: Date) -> str | None:
    if not date.complete:
        return None
    assert date.year
    assert date.month
    assert date.day
    return f"{date.year:04d}-{date.month:02d}-{date.day:02d}"


@final
class DateRangeSchema(Singleton, JsonLdObject):
    """
    A JSON Schema for :py:type:`betty.date.DateRange`.
    """

    def __init__(self):
        super().__init__(def_name="dateRange", title="Date range")
        date_schema = DateSchema()
        self._schema["additionalProperties"] = False
        self.add_property("start", OneOf(date_schema, Null(), title="Start date"))
        self.add_property("end", OneOf(date_schema, Null(), title="End date"))


@total_ordering
class DateRange(LinkedDataDumpableWithSchemaJsonLdObject):
    """
    A date range can describe a period of time between, before, after, or around start and/or end dates.
    """

    start: Date | None
    start_is_boundary: bool
    end: Date | None
    end_is_boundary: bool

    def __init__(
        self,
        start: Date | None = None,
        end: Date | None = None,
        start_is_boundary: bool = False,
        end_is_boundary: bool = False,
    ):
        self.start = start
        self.start_is_boundary = start_is_boundary
        self.end = end
        self.end_is_boundary = end_is_boundary

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

    def __contains__(self, other: DateLike) -> bool:
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

            for other in others:
                if self.start <= other:
                    return True
        elif self.end is not None:
            # Two date ranges with end dates only always overlap.
            if isinstance(other, DateRange) and other.start is None:
                return True

            for other in others:
                if other <= self.end:
                    return True
        return False

    @override
    async def dump_linked_data(
        self,
        project: Project,
        start_context_definition: str | None = None,
        end_context_definition: str | None = None,
    ) -> DumpMapping[Dump]:
        return {
            "start": await self.start.dump_linked_data(
                project, start_context_definition
            )
            if self.start
            else None,
            "end": await self.end.dump_linked_data(project, end_context_definition)
            if self.end
            else None,
        }

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project) -> DateRangeSchema:
        return DateRangeSchema()

    def _get_comparable_date(self, date: Date | None) -> Date | None:
        if date and date.comparable:
            return date
        return None

    _LT_DATE_RANGE_COMPARATORS = {
        (
            True,
            True,
            True,
            True,
        ): lambda self_start, self_end, other_start, other_end: self_start
        < other_start,
        (
            True,
            True,
            True,
            False,
        ): lambda self_start, self_end, other_start, other_end: self_start
        <= other_start,
        (
            True,
            True,
            False,
            True,
        ): lambda self_start, self_end, other_start, other_end: self_start < other_end
        or self_end <= other_end,
        (
            True,
            True,
            False,
            False,
        ): lambda self_start, self_end, other_start, other_end: NotImplemented,
        (
            True,
            False,
            True,
            True,
        ): lambda self_start, self_end, other_start, other_end: self_start
        < other_start,
        (
            True,
            False,
            True,
            False,
        ): lambda self_start, self_end, other_start, other_end: self_start
        < other_start,
        (
            True,
            False,
            False,
            True,
        ): lambda self_start, self_end, other_start, other_end: self_start < other_end,
        (
            True,
            False,
            False,
            False,
        ): lambda self_start, self_end, other_start, other_end: NotImplemented,
        (
            False,
            True,
            True,
            True,
        ): lambda self_start, self_end, other_start, other_end: self_end <= other_start,
        (
            False,
            True,
            True,
            False,
        ): lambda self_start, self_end, other_start, other_end: self_end <= other_start,
        (
            False,
            True,
            False,
            True,
        ): lambda self_start, self_end, other_start, other_end: self_end < other_end,
        (
            False,
            True,
            False,
            False,
        ): lambda self_start, self_end, other_start, other_end: NotImplemented,
        (
            False,
            False,
            True,
            True,
        ): lambda self_start, self_end, other_start, other_end: NotImplemented,
        (
            False,
            False,
            True,
            False,
        ): lambda self_start, self_end, other_start, other_end: NotImplemented,
        (
            False,
            False,
            False,
            True,
        ): lambda self_start, self_end, other_start, other_end: NotImplemented,
        (
            False,
            False,
            False,
            False,
        ): lambda self_start, self_end, other_start, other_end: NotImplemented,
    }

    _LT_DATE_COMPARATORS = {
        (True, True): lambda self_start, self_end, other: self_start < other,
        (True, False): lambda self_start, self_end, other: self_start < other,
        (False, True): lambda self_start, self_end, other: self_end <= other,
        (False, False): lambda self_start, self_end, other: NotImplemented,
    }

    def __lt__(self, other: Any) -> bool:
        if not isinstance(other, Date | DateRange):
            return NotImplemented

        self_start = self._get_comparable_date(self.start)
        self_end = self._get_comparable_date(self.end)
        signature = (
            self_start is not None,
            self_end is not None,
        )
        if isinstance(other, DateRange):
            other_start = self._get_comparable_date(other.start)
            other_end = self._get_comparable_date(other.end)
            return self._LT_DATE_RANGE_COMPARATORS[
                (
                    *signature,
                    other_start is not None,
                    other_end is not None,
                )
            ](self_start, self_end, other_start, other_end)
        return self._LT_DATE_COMPARATORS[signature](self_start, self_end, other)

    @override
    def __eq__(self, other: Any) -> bool:
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


@final
class DateLikeSchema(Singleton, OneOf):
    """
    A JSON Schema for :py:type:`betty.date.DateLike`.
    """

    def __init__(self):
        super().__init__(
            DateSchema(),
            DateRangeSchema(),
            def_name="dateLike",
            title="Date or date range",
        )


DateLike: TypeAlias = Date | DateRange
DatePartsFormatters: TypeAlias = Mapping[tuple[bool, bool, bool], str]
DateFormatters: TypeAlias = Mapping[tuple[bool | None], str]
DateRangeFormatters: TypeAlias = Mapping[
    tuple[bool | None, bool | None, bool | None, bool | None], str
]
