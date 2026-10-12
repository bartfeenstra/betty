"""
Media type validation.
"""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, final, overload

from betty.localizables.gettext import _
from betty.localizables.markup import do_you_mean
from betty.media_type import (
    MediaType,
    MediaTypeDefinition,
    ResolvableMediaType,
    resolve_media_type,
)
from betty.pathlib import StrPath
from betty.pipeline import Inlet, Pipeline
from betty.validators import InvalidValue

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.location import ResolvableLocation

type MediaTypeIndicator = ResolvableMediaType | StrPath
"""
A media type, or a file path or name that indicates a media type through its file extension.
"""


@final
class UnsupportedMediaType(InvalidValue[MediaType]):
    """
    Raised when a media type is not supported.
    """

    _message = _("Unsupported media type")

    def __init__(
        self,
        value: MediaType,
        media_types: Iterable[ResolvableMediaType],
        /,
        *,
        at: ResolvableLocation = (),
    ):
        super().__init__(
            value,
            at=at,
            hint=do_you_mean(
                *(
                    _("{media_type} ({media_type_label})").format(
                        media_type=media_type.type,
                        media_type_label=media_type.definition.label,
                    )
                    for media_type in map(resolve_media_type, media_types)
                )
            ),
        )


@final
class UnsupportedFileType(InvalidValue[StrPath]):
    """
    Raised when a file extension is not supported.
    """

    _message = _("Unsupported file type")

    def __init__(
        self,
        value: StrPath,
        media_types: Iterable[ResolvableMediaType],
        /,
        *,
        at: ResolvableLocation = (),
    ):
        super().__init__(
            value,
            at=at,
            hint=do_you_mean(
                *(
                    _("{media_type} ({media_type_label})").format(
                        media_type=extension,
                        media_type_label=media_type.definition.label,
                    )
                    for media_type in map(resolve_media_type, media_types)
                    for extension in media_type.extensions
                )
            ),
        )


@overload
def is_media_type(
    *, media_types: Iterable[ResolvableMediaType]
) -> Pipeline[MediaTypeIndicator, MediaType]:
    pass


@overload
def is_media_type(
    value: MediaTypeIndicator, /, *, media_types: Iterable[ResolvableMediaType]
) -> MediaType:
    pass


def is_media_type(*value_, media_types):
    """
    Validate a media type.
    """
    media_types = tuple(map(resolve_media_type, media_types))
    if value_:
        (value,) = value_
        if isinstance(value, MediaType | MediaTypeDefinition):
            value_media_type = resolve_media_type(value)
            for media_type in media_types:
                if media_type == value_media_type:
                    return media_type
            raise UnsupportedMediaType(value_media_type, media_types)
        value_str = str(value)
        for media_type in media_types:
            for extension in media_type.extensions:
                if value_str.endswith(extension):
                    return media_type
        raise UnsupportedFileType(value, media_types)
    return Inlet(partial(is_media_type, media_types=media_types))
