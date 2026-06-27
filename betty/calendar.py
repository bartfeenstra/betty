"""
The calendar API.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, final

if TYPE_CHECKING:
    from collections.abc import Sequence

    from betty.localizable import Localizable
    from betty.machine_name import MachineName


class Calendar(ABC):
    """
    A calendar.
    """

    @final
    def __init_subclass__(cls, **kwargs: Any):
        assert cls.__module__.startswith("betty.calendars."), (
            "Third-party calendars are not supported."
        )
        super().__init_subclass__(**kwargs)

    @classmethod
    @abstractmethod
    def id(cls) -> MachineName:
        """
        The unique calendar ID.
        """

    @classmethod
    @abstractmethod
    def label(cls) -> Localizable:
        """
        The human-readable calendar label.
        """

    @classmethod
    @abstractmethod
    def public_label(cls) -> Localizable:
        """
        The human-readable public calendar label.
        """

    @classmethod
    @abstractmethod
    def years(cls) -> Sequence[int]:
        """
        Get the years on this calendar.
        """

    @classmethod
    @abstractmethod
    def months(cls) -> int:
        """
        Get the number of months in a year.
        """

    @classmethod
    @abstractmethod
    def days(cls, year: int | None, month: int | None, /) -> int:
        """
        Get the number of days for the given month, or the maximum number of days any month could have.
        """

    # @todo Should we be using this at all? It's too simplistic, because it cannot handle the new year not
    # @todo being on the first day of the frst month.
    # @todo
    # @todo Can we refactor this using cls.earliest() and cls.latest()?
    # @todo
    @classmethod
    def validate(
        cls, year: int | None, month: int | None, day: int | None, /
    ) -> bool | None:
        """
        Validate the given date against this calendar.

        Return ``True`` if all date parts are present and valid. Return ``False`` if any date part is invalid. Return
        ``None`` otherwise, indicating that any given date was valid, but not all data was given.
        """
        if year is not None and year not in cls.years():
            return False
        if month is not None:
            if month < 1:
                return False
            if month > cls.months():
                return False
        if day is not None:
            if day < 1:
                return False
            if day > cls.days(year, month):
                return False
        if year is None:
            return None
        if month is None:
            return None
        if day is None:
            return None
        return True

    @classmethod
    @abstractmethod
    def to_proleptic_iso8601(
        cls, year: int, month: int, day: int, /
    ) -> tuple[int, int, int]:
        """
        Convert a date on this calendar to one on the :py:class:`proleptic ISO 8601 calendar <betty.calendars.iso8601.ProlepticIso8601>`.
        """

    @classmethod
    def earliest(
        cls, year: int | None, month: int | None, day: int | None, /
    ) -> tuple[int | None, int | None, int | None]:
        """
        Try to fill in the missing date parts with the earliest possible values.
        """
        return year, month, day

    @classmethod
    def latest(
        cls, year: int | None, month: int | None, day: int | None, /
    ) -> tuple[int | None, int | None, int | None]:
        """
        Try to fill in the missing date parts with the latest possible values.
        """
        return year, month, day


def to_year_zero(year: int, /) -> int:
    """
    Convert a year from a numbering without year zero to a numbering with year zero.
    """
    raise NotImplementedError
