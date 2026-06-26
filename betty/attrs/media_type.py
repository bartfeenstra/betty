"""
Media type attributes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from betty.attrs.owner import OwnerAttr
from betty.attrs.privacy import HasPrivacy
from betty.datas.aggregate.record import FieldDefinition
from betty.json_schemas.media_type import MediaTypeSchema
from betty.linked_data import JsonLdObject, LinkedDataDumpableWithSchemaJsonLdObject
from betty.media_type import MediaType, ResolvableMediaType, resolve_media_type
from betty.prop import HasProps

if TYPE_CHECKING:
    from betty.attrs.common import CommonAttr
    from betty.localizable import ResolvableLocalizable
    from betty.portable import PortableMapping
    from betty.project import Project


def new_media_type_attr(
    *,
    label: ResolvableLocalizable | None = None,
    description: ResolvableLocalizable | None = None,
) -> CommonAttr[HasProps, MediaType, ResolvableMediaType]:
    """
    Create an attribute containing a media type.
    """
    return OwnerAttr(
        FieldDefinition(MediaType, label=label, description=description)
    ).setter(resolve_media_type)


class HasMediaType(LinkedDataDumpableWithSchemaJsonLdObject, HasProps):
    """
    A resource with an `IANA media type <https://www.iana.org/assignments/media-types/media-types.xhtml>`_.
    """

    media_type = new_media_type_attr().optional

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
        if (
            not isinstance(self, HasPrivacy) or self.public
        ) and self.media_type is not None:
            portable["mediaType"] = str(self.media_type)
        return portable

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project, /) -> JsonLdObject:
        schema = await super().linked_data_schema(project)
        schema.add_property("mediaType", MediaTypeSchema(), False)
        return schema
