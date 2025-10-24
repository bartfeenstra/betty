"""
Date types with dates.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from typing_extensions import override

from betty.date import Date, DateLike, DateLikeSchema
from betty.json.linked_data import (
    JsonLdObject,
    LinkedDataDumpableWithSchemaJsonLdObject,
)
from betty.privacy import is_public

if TYPE_CHECKING:
    from betty.project import Project
    from betty.serde.dump import Dump, DumpMapping


class HasDate(LinkedDataDumpableWithSchemaJsonLdObject):
    """
    A resource with date information.
    """

    def __init__(
        self,
        *args: Any,
        date: DateLike | None = None,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self.date = date

    def dated_linked_data_contexts(self) -> tuple[str | None, str | None, str | None]:
        """
        Get the JSON-LD context term definition IRIs for the possible dates.

        :returns: A 3-tuple with the IRI for a single date, a start date, and an end date, respectively.
        """
        return None, None, None

    @override
    async def dump_linked_data(self, project: Project) -> DumpMapping[Dump]:
        dump = await super().dump_linked_data(project)
        if self.date and is_public(self):
            (
                schema_org_date_definition,
                schema_org_start_date_definition,
                schema_org_end_date_definition,
            ) = self.dated_linked_data_contexts()
            if isinstance(self.date, Date):
                dump["date"] = await self.date.dump_linked_data(
                    project, schema_org_date_definition
                )
            else:
                dump["date"] = await self.date.dump_linked_data(
                    project,
                    schema_org_start_date_definition,
                    schema_org_end_date_definition,
                )
        return dump

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project) -> JsonLdObject:
        schema = await super().linked_data_schema(project)
        schema.add_property("date", DateLikeSchema(), False)
        return schema
