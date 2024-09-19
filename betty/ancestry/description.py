"""
Data types with human-readable description texts.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from typing_extensions import override

from betty.json.linked_data import LinkedDataDumpable, dump_context
from betty.json.schema import Object
from betty.locale.localizable import (
    OptionalStaticTranslationsLocalizableAttr,
    ShorthandStaticTranslations,
    StaticTranslationsLocalizableSchema,
)

if TYPE_CHECKING:
    from betty.serde.dump import DumpMapping, Dump
    from betty.project import Project


class HasDescription(LinkedDataDumpable[Object]):
    """
    A resource with a description.
    """

    #: The human-readable description.
    description = OptionalStaticTranslationsLocalizableAttr("description")

    def __init__(
        self,
        *args: Any,
        description: ShorthandStaticTranslations | None = None,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        if description is not None:
            self.description.replace(description)

    @override
    async def dump_linked_data(self, project: Project) -> DumpMapping[Dump]:
        dump = await super().dump_linked_data(project)
        if self.description:
            dump["description"] = await self.description.dump_linked_data(project)
            dump_context(dump, description="https://schema.org/description")
        return dump

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project) -> Object:
        schema = await super().linked_data_schema(project)
        schema.add_property("description", StaticTranslationsLocalizableSchema(), False)
        return schema
