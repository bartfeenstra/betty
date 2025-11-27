"""
JSON schemas for the date API.
"""

from __future__ import annotations

from typing import final

from betty.classtools import Singleton
from betty.json.linked_data import JsonLdObject
from betty.json.schema import Boolean, Null, Number, OneOf, String


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
