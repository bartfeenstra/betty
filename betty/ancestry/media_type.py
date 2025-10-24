"""
Data types that have media types.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from typing_extensions import override

from betty.json.linked_data import (
    JsonLdObject,
    LinkedDataDumpableWithSchemaJsonLdObject,
)
from betty.media_type import MediaType, MediaTypeSchema
from betty.privacy import is_public

if TYPE_CHECKING:
    from betty.project import Project
    from betty.serde.dump import Dump, DumpMapping


class HasMediaType(LinkedDataDumpableWithSchemaJsonLdObject):
    """
    A resource with an `IANA media type <https://www.iana.org/assignments/media-types/media-types.xhtml>`_.
    """

    def __init__(
        self,
        *args: Any,
        media_type: MediaType | None = None,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self.media_type = media_type

    @override
    async def dump_linked_data(self, project: Project) -> DumpMapping[Dump]:
        dump = await super().dump_linked_data(project)
        if is_public(self) and self.media_type is not None:
            dump["mediaType"] = str(self.media_type)
        return dump

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project) -> JsonLdObject:
        schema = await super().linked_data_schema(project)
        schema.add_property("mediaType", MediaTypeSchema(), False)
        return schema
