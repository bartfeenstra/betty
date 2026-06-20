"""
JSON schemas for the date API.
"""

from __future__ import annotations

from typing import final

from betty.json_schema import Boolean, Null, Number, OneOf, String
from betty.linked_data import JsonLdObject


@final
class DateSchema(JsonLdObject):
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


@final
class DateRangeSchema(JsonLdObject):
    """
    A JSON Schema for :py:type:`betty.date.DateRange`.
    """

    def __init__(self):
        super().__init__(def_name="dateRange", title="Date range")
        date_schema = DateSchema()
        self.schema["additionalProperties"] = False
        self.add_property("start", OneOf(date_schema, Null(), title="Start date"))
        self.add_property("end", OneOf(date_schema, Null(), title="End date"))


@final
class ResolvableDateSchema(OneOf):
    """
    A JSON Schema for :py:type:`betty.date.AnyDate`.
    """

    def __init__(self):
        super().__init__(
            DateSchema(),
            DateRangeSchema(),
            def_name="dateLike",
            title="Date or date range",
        )
