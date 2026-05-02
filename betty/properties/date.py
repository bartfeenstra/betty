"""
Date properties.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, final, override

from betty.datas.date import AnyDateDefinition
from betty.date import ANY_DATE_SCHEMA, AnyDate, Date, DateRange
from betty.linked_data import LinkedDataDumper
from betty.portable import PortableData
from betty.property import Optional, Property

if TYPE_CHECKING:
    from betty.json_schema import Schema
    from betty.portable import PortableMapping
    from betty.project import Project


@final
class HasAnyDateProperty(Property, LinkedDataDumper[AnyDate, PortableData]):
    def __init__(self):
        super().__init__(AnyDateDefinition())

    @override
    async def linked_data_schema_for(self, project: Project, /) -> Schema:
        return ANY_DATE_SCHEMA

    @override
    async def dump_linked_data_for(
        self, project: Project, target: AnyDate, /
    ) -> PortableData:
        if isinstance(target, Date):
            return self._dump_linked_data_for_date(target)
        return self._dump_linked_data_for_date_range(target)

    def _dump_linked_data_for_date(self, date: Date, /) -> PortableMapping:
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
            portable["iso8601"] = self._dump_date_iso8601(date)
        return portable

    def _dump_linked_data_for_date_range(
        self, date_range: DateRange, /
    ) -> PortableMapping:
        return {
            "start": self._dump_linked_data_for_date(date_range.start)
            if date_range.start
            else None,
            "end": self._dump_linked_data_for_date(date_range.end)
            if date_range.end
            else None,
        }

    def _dump_date_iso8601(self, date: Date, /) -> str | None:
        if not date.complete:
            return None
        assert date.year
        assert date.month
        assert date.day
        return f"{date.year:04d}-{date.month:02d}-{date.day:02d}"


class HasAnyDate:
    """
    A resource with date information.
    """

    date = Optional(HasAnyDateProperty())
    """
    The date.
    """

    def __init__(
        self,
        *args: Any,
        date: AnyDate | None = None,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self.date = date
