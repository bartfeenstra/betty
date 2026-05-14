"""
Media type properties.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, final, override

from betty.attrs.attr import AttrAttr
from betty.attrs.optional import Optional
from betty.linked_data import JsonLdObject, LinkedDataDumpableWithSchemaJsonLdObject
from betty.media_type import MediaType, ResolvableMediaType, resolve_media_type
from betty.media_type.schema import MediaTypeSchema
from betty.privacy.resolve import is_public
from betty.property import HasProperties

if TYPE_CHECKING:
    from collections.abc import Callable

    from betty.locale.localizable import ResolvableLocalizable
    from betty.portable import PortableMapping
    from betty.project import Project


@final
class MediaTypeAttr(AttrAttr[HasProperties, MediaType, ResolvableMediaType]):
    """
    An attribute containing a media type.
    """

    def __init__(
        self,
        *,
        label: ResolvableLocalizable | None = None,
        default: Callable[[], MediaType] | None = None,
        description: ResolvableLocalizable | None = None,
        omit_load: bool | None = None,
        omit_dump: Callable[[MediaType], bool] | None = None,
    ):
        super().__init__(
            data=MediaType,
            default=default,
            label=label,
            description=description,
            omit_load=omit_load,
            omit_dump=omit_dump,
            resolver=resolve_media_type,
        )


class HasMediaType(LinkedDataDumpableWithSchemaJsonLdObject, HasProperties):
    """
    A resource with an `IANA media type <https://www.iana.org/assignments/media-types/media-types.xhtml>`_.
    """

    media_type = Optional(MediaTypeAttr())

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
