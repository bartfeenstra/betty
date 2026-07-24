"""
Reusable calendars.
"""

from collections.abc import Iterable, Mapping
from typing import Final, final

from betty.calendar import Calendar
from betty.calendars.gregorian import Gregorian, ProlepticGregorian
from betty.calendars.iso8601 import Iso8601, ProlepticIso8601
from betty.calendars.julian import Julian, ProlepticJulian
from betty.exception import HumanFacingException
from betty.localizables.gettext import _
from betty.localizables.markup import Paragraph, do_you_mean
from betty.machine_name import MachineName

calendars: Final[Iterable[type[Calendar]]] = (
    Gregorian,
    Iso8601,
    Julian,
    ProlepticGregorian,
    ProlepticIso8601,
    ProlepticJulian,
)
"""
The available calendars. 
"""

_calendars: Final[Mapping[MachineName, type[Calendar]]] = {
    calendar.id(): calendar for calendar in calendars
}


def get(calendar: MachineName, /) -> type[Calendar]:
    """
    Get a calendar by its ID.

    :raises CalendarNotFound:
    """
    try:
        return _calendars[calendar]
    except KeyError:
        raise CalendarNotFound(calendar) from None


@final
class CalendarNotFound(HumanFacingException, ValueError):
    """
    Raised when a calendar cannot be found.
    """

    def __init__(self, calendar: MachineName, /):
        super().__init__(
            Paragraph(
                _('Cannot find the "{calendar}" calendar.').format(calendar=calendar),
                do_you_mean(calendar.id() for calendar in calendars),
            )
        )
