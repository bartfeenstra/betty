"""
Date attributes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from betty.attr import Object
from betty.attrs.owner import OwnerAttr
from betty.attrs.privacy import HasPrivacy
from betty.datas.aggregate.record.object import ObjectDefinition
from betty.datas.date import AnyDateDefinition
from betty.date import AnyDate, Date, DateRange, _dump_date_iso8601
from betty.linked_data import LinkedData
from betty.typing import Voidable, VoidableType, VoidType

if TYPE_CHECKING:
    from collections.abc import Mapping

    from betty.portable import PortableMapping
    from betty.project import Project


class HasAnyDate[DataDefinitionT: ObjectDefinition = ObjectDefinition](
    Object[DataDefinitionT]
):
    """
    A resource with date information.
    """

    date = OwnerAttr(AnyDateDefinition()).optional
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

    @override
    @classmethod
    async def linked_data_schema_properties(
        cls, project: Project, /
    ) -> Mapping[str, VoidableType[PortableMapping]]:
        return {
            "date": Voidable({
                "$ref": "#/$defs/anyDate",
                "$defs": {
                    "date": {
                        "title": "Date",
                        "type": "object",
                        "properties": {
                            "fuzzy": {
                                "title": "Fuzzy",
                                "type": "bool",
                            },
                            "year": {
                                "title": "Year",
                                "type": "number",
                            },
                            "month": {
                                "title": "Month",
                                "type": "number",
                            },
                            "day": {
                                "title": "Day",
                                "type": "number",
                            },
                            "iso8601": {
                                "pattern": "^\\d\\d\\d\\d-\\d\\d-\\d\\d$",
                                "title": "ISO 8601",
                                "type": "string",
                            },
                        },
                        "requiredProperties": ["fuzzy"],
                    },
                    "dateRange": {
                        "additionalProperties": False,
                        "start": {
                            "oneOf": [
                                {
                                    "$ref": "#/$defs/date",
                                },
                                {
                                    "type": "null",
                                },
                            ],
                            "title": "Start date",
                        },
                        "end": {
                            "oneOf": [
                                {
                                    "$ref": "#/$defs/date",
                                },
                                {
                                    "type": "null",
                                },
                            ],
                            "title": "End date",
                        },
                        "title": "Date range",
                        "type": "object",
                    },
                    "anyDate": {
                        "oneOf": [
                            {
                                "$ref": "#/$defs/date",
                            },
                            {
                                "$ref": "#/$defs/dateRange",
                            },
                        ],
                        "title": "Date or date range",
                    },
                },
            })
        }

    @override
    async def dump_linked_data_properties(
        self, project: Project, /
    ) -> Mapping[str, LinkedData | VoidType]:
        if not self.date:
            return {}
        if isinstance(self, HasPrivacy) and self.private:
            return {}
        if isinstance(self.date, Date):
            return {
                "date": LinkedData(
                    _dump_linked_data_for_date(
                        self.date, "https://schema.org/startDate"
                    )
                )
            }
        return {"date": LinkedData(_dump_linked_data_for_date_range(self.date))}


def _dump_linked_data_for_date(date: Date, context: str) -> PortableMapping:
    data: PortableMapping = {
        "@context": {
            "iso8601": context,
        },
        "fuzzy": date.fuzzy,
    }
    if date.year:
        data["year"] = date.year
    if date.month:
        data["month"] = date.month
    if date.day:
        data["day"] = date.day
    if date.comparable:
        data["iso8601"] = _dump_date_iso8601(date)
    return data


def _dump_linked_data_for_date_range(date_range: DateRange) -> PortableMapping:
    return {
        "start": _dump_linked_data_for_date(
            date_range.start, "https://schema.org/startDate"
        )
        if date_range.start
        else None,
        "end": _dump_linked_data_for_date(date_range.end, "https://schema.org/endDate")
        if date_range.end
        else None,
    }
