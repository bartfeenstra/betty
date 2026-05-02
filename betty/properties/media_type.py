"""
Media type properties.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, final, override

from betty.linked_data import LinkedDataDumper
from betty.media_type import (
    MEDIA_TYPE_SCHEMA,
    MediaType,
    ResolvableMediaType,
    resolve_media_type,
)
from betty.property import Optional, Property

if TYPE_CHECKING:
    from collections.abc import Callable

    from betty.json_schema import Schema
    from betty.locale.localizable import ResolvableLocalizable
    from betty.project import Project


@final
class MediaTypeProperty(
    Property[MediaType, ResolvableMediaType], LinkedDataDumper[MediaType, str]
):
    """
    A property containing a media type.
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

    @override
    async def linked_data_schema_for(self, project: Project, /) -> Schema:
        return MEDIA_TYPE_SCHEMA

    @override
    async def dump_linked_data_for(self, project: Project, target: MediaType, /) -> str:
        return str(target)


class HasMediaType:
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
