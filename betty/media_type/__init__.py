"""
Provide `media type <https://en.wikipedia.org/wiki/Media_type>`_ handling utilities.
"""

from __future__ import annotations

from email.policy import EmailPolicy
from pathlib import Path
from typing import final, TYPE_CHECKING, TypeAlias, Union, cast

from typing_extensions import override

from betty.json.schema import String

if TYPE_CHECKING:
    from collections.abc import Sequence


class UnsupportedMediaType(ValueError):
    """
    Raised when a media type is not supported.
    """

    pass  # pragma: no cover


#: A media type, or a file path or name that indicates a media type through its file extension.
MediaTypeIndicator: TypeAlias = Union["MediaType", Path, str]


@final
class MediaType:
    """
    Define a `media type <https://en.wikipedia.org/wiki/Media_type>`_.

    Media types are also commonly known as content types or MIME types.
    """

    _suffix: str | None

    def __init__(
        self, media_type: str, *, file_extensions: Sequence[str] | None = None
    ):
        normalized_media_type = cast(
            str, EmailPolicy.header_factory("Content-Type", media_type).content_type
        )
        self._type, normalized_media_type_remainder = normalized_media_type.split("/")
        plus_position = normalized_media_type_remainder.find("+")
        if plus_position > 0:
            self._subtype = normalized_media_type_remainder[0:plus_position]
            self._suffix = normalized_media_type_remainder[plus_position:]
        else:
            self._subtype = normalized_media_type_remainder
            self._suffix = None
        self._file_extensions = file_extensions or ()

    def __hash__(self) -> int:
        return hash((self._type, self._subtype, self._suffix, self._file_extensions))

    @property
    def type(self) -> str:
        """
        The type, e.g. ``application`` for ``application/ld+json``.
        """
        return self._type

    @property
    def subtype(self) -> str:
        """
        The subtype, e.g. ``"vnd.oasis.opendocument.text"`` for ``"application/vnd.oasis.opendocument.text"``.
        """
        return self._subtype

    @property
    def suffix(self) -> str | None:
        """
        The suffix, e.g. ``json`` for ``application/ld+json``.
        """
        return self._suffix

    # @todo Do we use or need this at all?
    # @todo How would we test for that because #)(%*&(#$*%& object has a default __str__() implementation?
    # @todo OH! Just raise an exception!
    @override
    def __str__(self) -> str:
        return f"{self.type}/{self.subtype}{self.suffix or ''}"

    @property
    def file_extensions(self) -> Sequence[str]:
        """
        The file extensions associated with this media type.
        """
        return list(self._file_extensions)

    @property
    def preferred_file_extension(self) -> str:
        """
        The preferred extension for files containing content of this media type.
        """
        try:
            return self.file_extensions[0]
        except IndexError:
            return ""

    def match(self, other: MediaType)->MediaType:
        


@final
class MediaTypeSchema(String):
    """
    A JSON Schema for :py:class:`betty.media_type.MediaType`.
    """

    def __init__(self):
        super().__init__(
            def_name="mediaType",
            title="Media type",
            description="An IANA media type (https://www.iana.org/assignments/media-types/media-types.xhtml).",
        )
