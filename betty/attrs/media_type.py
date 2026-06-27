"""
Media type attributes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from betty.attr import Object
from betty.attrs.owner import OwnerAttr
from betty.attrs.privacy import HasPrivacy
from betty.datas.aggregate.record import FieldDefinition
from betty.datas.aggregate.record.object import ObjectDefinition
from betty.linked_data import LinkedData
from betty.media_type import MediaType, ResolvableMediaType, resolve_media_type
from betty.typing import Voidable, VoidableType

if TYPE_CHECKING:
    from collections.abc import Mapping

    from betty.attrs.common import CommonAttr
    from betty.localizable import ResolvableLocalizable
    from betty.portable import PortableMapping
    from betty.project import Project
    from betty.typing import VoidType


def new_media_type_attr(
    *,
    label: ResolvableLocalizable | None = None,
    description: ResolvableLocalizable | None = None,
) -> CommonAttr[Object, MediaType, ResolvableMediaType]:
    """
    Create an attribute containing a media type.
    """
    return OwnerAttr(
        FieldDefinition(MediaType, label=label, description=description)
    ).setter(resolve_media_type)


class HasMediaType[DataDefinitionT: ObjectDefinition = ObjectDefinition](
    Object[DataDefinitionT]
):
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
    @classmethod
    async def linked_data_schema_properties(
        cls, project: Project, /
    ) -> Mapping[str, VoidableType[PortableMapping]]:
        return {
            "mediaType": Voidable({
                "$ref": {
                    "oneOf": [
                        {
                            "#/$defs/mediaType",
                        },
                        {
                            "type": "null",
                        },
                    ],
                },
                "$defs": {
                    "mediaType": {
                        "description": "An IANA media type (https://www.iana.org/assignments/media-types/media-types.xhtml).",
                        "title": "Media type",
                        "type": "string",
                    }
                },
            }),
        }

    @override
    async def dump_linked_data_properties(
        self, project: Project, /
    ) -> Mapping[str, LinkedData | VoidType]:
        if isinstance(self, HasPrivacy) and self.private:
            return {}
        return {
            "mediaType": LinkedData(str(self.media_type) if self.media_type else None)
        }
