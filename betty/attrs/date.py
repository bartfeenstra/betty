"""
Date attributes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from betty.attrs.owner import OwnerAttr
from betty.attrs.privacy import HasPrivacy
from betty.datas.date import DateExpressionDefinition
from betty.date import Date, DateExpression
from betty.json_schemas.date import DateExpressionSchema
from betty.linked_data import JsonLdObject, LinkedDataDumpableWithSchemaJsonLdObject
from betty.prop import HasProps

if TYPE_CHECKING:
    from betty.portable import PortableMapping
    from betty.project import Project
from betty.date import DateRange
from betty.linked_data import dump_context


class HasDate(LinkedDataDumpableWithSchemaJsonLdObject, HasProps):
    """
    A resource with a date.
    """

    date = OwnerAttr(DateExpressionDefinition()).optional
    """
    The date.
    """

    def __init__(
        self,
        *args: Any,
        date: DateExpression | None = None,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self.date = date

    def has_date_linked_data_contexts(
        self,
    ) -> tuple[str | None, str | None, str | None]:
        """
        Get the JSON-LD context term definition IRIs for the possible dates.

        :returns: A 3-tuple with the IRI for a single date, a start date, and an end date, respectively.
        """
        return None, None, None

    @override
    async def dump_linked_data(self, project: Project, /) -> PortableMapping:
        portable = await super().dump_linked_data(project)
        if self.date and (not isinstance(self, HasPrivacy) or self.public):
            (
                schema_org_date_definition,
                schema_org_start_date_definition,
                schema_org_end_date_definition,
            ) = self.has_date_linked_data_contexts()
            if isinstance(self.date, Date):
                portable["date"] = _dump_linked_data_for_date(
                    self.date, context_definition=schema_org_date_definition
                )
            else:
                portable["date"] = _dump_linked_data_for_date_range(
                    self.date,
                    start_context_definition=schema_org_start_date_definition,
                    end_context_definition=schema_org_end_date_definition,
                )
        return portable

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project, /) -> JsonLdObject:
        schema = await super().linked_data_schema(project)
        schema.add_property("date", DateExpressionSchema(), False)
        return schema


def _dump_linked_data_for_date(
    date: Date, *, context_definition: str | None = None
) -> PortableMapping:
    portable: PortableMapping = {
        "imprecise": date.imprecise,
    }
    if date.year:
        portable["year"] = date.year
    if date.month:
        portable["month"] = date.month
    if date.day:
        portable["day"] = date.day
    if date.year and date.month and date.day:
        portable["date"] = (
            f"{'-' if date.year < 0 else '-'}{date.year:04d}-{date.month:02d}-{date.day:02d}"
        )
        # Set a single term definition because JSON-LD does not let us apply multiple
        # for the same term (key).
        if context_definition:
            dump_context(portable, date=context_definition)
    return portable


def _dump_linked_data_for_date_range(
    date_range: DateRange,
    *,
    start_context_definition: str | None = None,
    end_context_definition: str | None = None,
) -> PortableMapping:
    return {
        "start": _dump_linked_data_for_date(
            date_range.start, context_definition=start_context_definition
        )
        if date_range.start
        else None,
        "end": _dump_linked_data_for_date(
            date_range.end, context_definition=end_context_definition
        )
        if date_range.end
        else None,
    }
