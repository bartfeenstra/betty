"""
Data types with human-readable description texts.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from typing_extensions import override

from betty.json.linked_data import (
    JsonLdObject,
    LinkedDataDumpableWithSchemaJsonLdObject,
    dump_context,
)
from betty.locale.localizable import StaticTranslations
from betty.privacy import is_public

if TYPE_CHECKING:
    from betty.locale.localizable import Localizable
    from betty.project import Project
    from betty.serde.dump import Dump, DumpMapping


class HasDescription(LinkedDataDumpableWithSchemaJsonLdObject):
    """
    A resource with a description.
    """

    def __init__(
        self,
        *args: Any,
        description: Localizable | None = None,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self.description = description

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project) -> JsonLdObject:
        schema = await super().linked_data_schema(project)
        schema.add_property(
            "description",
            await StaticTranslations.linked_data_schema(project),
            False,
        )
        return schema

    @override
    async def dump_linked_data(self, project: Project) -> DumpMapping[Dump]:
        dump = await super().dump_linked_data(project)
        dump_context(dump, description="https://schema.org/description")
        if self.description is not None and is_public(self):
            dump["description"] = await StaticTranslations.dump_linked_data_for(
                project, self.description
            )
        return dump
