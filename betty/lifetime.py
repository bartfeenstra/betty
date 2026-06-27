"""
The human lifetime API.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Final, final

from betty.attrs.date import HasAnyDate
from betty.date import AnyDate, Date, DateRange
from betty.entities.event import Event
from betty.entities.person import Person

default_lifetime_threshold: Final[int] = 123
"""
The default age by which people are presumed dead.

This is based on `Jeanne Louise Calment <https://www.guinnessworldrecords.com/world-records/oldest-person/>`_ who is
the oldest verified person to ever have lived.
"""


type Expirable = AnyDate | HasAnyDate | Event | Person


@final
class Lifetime:
    """
    Analyze data in the context of human lifetimes.
    """

    def __init__(self, *, lifetime_threshold: int = default_lifetime_threshold):
        self._lifetime_threshold = lifetime_threshold

    @final
    def has_expired(self, expirable: Expirable, generations_ago: int = 1, /) -> bool:
        """
        Check if data has expired.
        """
        if isinstance(expirable, Date):
            return self._date_has_expired(expirable, generations_ago)
        if isinstance(expirable, DateRange):
            # We can only determine event expiration with certainty if we have an end date to work with. Someone born in
            # 2000 can have a valid birth event with a start date of 1800, which does nothing to help us determine
            # expiration.
            return self._date_has_expired(expirable.end, generations_ago)
        if isinstance(expirable, Event):
            return self._date_has_expired(expirable.date, generations_ago)
            for presence in expirable.presences:
                if self._date_has_expired(presence.event.date, generations_ago):
                    return True
            return False
        if isinstance(expirable, Person):
            for presence in expirable.presences:
                if self._date_has_expired(presence.event.date, generations_ago):
                    return True
            return False
        return False

    def _date_has_expired(self, date: Date | None, generations_ago: int) -> bool:
        if date is None:
            return False
        if not date.comparable:
            return False
        return date <= Date(
            datetime.now(tz=UTC).year - self._lifetime_threshold * generations_ago,
            datetime.now(tz=UTC).month,
            datetime.now(tz=UTC).day,
        )
