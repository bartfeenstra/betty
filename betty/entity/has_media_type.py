"""
Data types that have media types.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from betty.linked_data import (
    JsonLdObject,
    LinkedDataDumpableWithSchemaJsonLdObject,
)
from betty.media_type import MediaTypeProperty, ResolvableMediaType
from betty.media_type.schema import MediaTypeSchema
from betty.privacy import is_public
from betty.property import Optional

if TYPE_CHECKING:
    from betty.portable import PortableMapping
    from betty.project import Project


class HasMediaType(LinkedDataDumpableWithSchemaJsonLdObject):
    """
    A resource with an `IANA media type <https://www.iana.org/assignments/media-types/media-types.xhtml>`_.
    """

    media_type = Optional(MediaTypeProperty())

    def __init__(
        self,
        *args: Any,
        media_type: ResolvableMediaType | None = None,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self.media_type = media_type

    @override
    async def dump_linked_data(self, project: Project, /) -> PortableMapping:
        portable = await super().dump_linked_data(project)
        if is_public(self) and self.media_type is not None:
            portable["mediaType"] = str(self.media_type)
        return portable

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project, /) -> JsonLdObject:
        schema = await super().linked_data_schema(project)
        schema.add_property("mediaType", MediaTypeSchema(), False)
        return schema
