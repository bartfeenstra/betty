"""
Linked data for the date API.
"""

from betty.date import Date, DateRange, _dump_date_iso8601
from betty.json.linked_data import dump_context
from betty.portable import PortableMapping


def dump_linked_data_for_date(
    date: Date, *, context_definition: str | None = None
) -> PortableMapping:
    """
    Dump a date to linked data.
    """
    linked_data = {
        "fuzzy": date.fuzzy,
    }
    if date.year:
        linked_data["year"] = date.year
    if date.month:
        linked_data["month"] = date.month
    if date.day:
        linked_data["day"] = date.day
    if date.comparable:
        linked_data["iso8601"] = _dump_date_iso8601(date)
        # Set a single term definition because JSON-LD does not let us apply multiple
        # for the same term (key).
        if context_definition:
            dump_context(linked_data, iso8601=context_definition)
    return linked_data


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
