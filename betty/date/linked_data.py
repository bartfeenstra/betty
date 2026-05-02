"""
Linked data for the date API.
"""

from betty.date import Date, DateRange, _dump_date_iso8601
from betty.linked_data import dump_context
from betty.portable import PortableMapping


def dump_linked_data_for_date(
    date: Date, *, context_definition: str | None = None
) -> PortableMapping:
    """
    Dump a date to linked data.
    """
    portable: PortableMapping = {
        "fuzzy": date.fuzzy,
    }
    if date.year:
        portable["year"] = date.year
    if date.month:
        portable["month"] = date.month
    if date.day:
        portable["day"] = date.day
    if date.comparable:
        portable["iso8601"] = _dump_date_iso8601(date)
        # Set a single term definition because JSON-LD does not let us apply multiple
        # for the same term (key).
        if context_definition:
            dump_context(portable, iso8601=context_definition)
    return portable


def dump_linked_data_for_date_range(
    date_range: DateRange,
    *,
    start_context_definition: str | None = None,
    end_context_definition: str | None = None,
) -> PortableMapping:
    """
    Dump a date range to linked data.
    """
    return {
        "start": dump_linked_data_for_date(
            date_range.start, context_definition=start_context_definition
        )
        if date_range.start
        else None,
        "end": dump_linked_data_for_date(
            date_range.end, context_definition=end_context_definition
        )
        if date_range.end
        else None,
    }
