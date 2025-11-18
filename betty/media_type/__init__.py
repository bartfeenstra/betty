"""
Provide `media type <https://en.wikipedia.org/wiki/Media_type>`_ handling utilities.
"""

from __future__ import annotations

from email.message import EmailMessage
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypeAlias, final

from typing_extensions import override

from betty.classtools import Singleton
from betty.json.schema import String

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence


class InvalidMediaType(ValueError):
    """
    Raised when an identifier is not a valid media type.
    """


class UnsupportedMediaType(RuntimeError):
    """
    Raised when a media type is not supported.
    """

    def __init__(self, media_type: MediaTypeIndicator):
        super().__init__(f"Unsupported media type: {media_type}")


@final
class MediaType:
    """
    Define a `media type <https://en.wikipedia.org/wiki/Media_type>`_.

    Media types are also commonly known as content types or MIME types.
    """

    _suffix: str | None

    def __init__(self, media_type: str, *, extensions: Sequence[str] | None = None):
        self._str = media_type
        message = EmailMessage()
        message["Content-Type"] = media_type
        type_part = message.get_content_type()
        # EmailMessage.get_content_type() always returns a type, and will fall back to alternatives if the header is
        # invalid.
        if not media_type.startswith(type_part):
            raise InvalidMediaType(f'"{media_type}" is not a valid media type.')
        self._parameters: Mapping[str, str] = dict(message["Content-Type"].params)
        self._type, type_part_remainder = type_part.split("/")
        if not type_part_remainder:
            raise InvalidMediaType("The subtype must not be empty.")
        plus_position = type_part_remainder.find("+")
        if plus_position > 0:
            self._subtype = type_part_remainder[0:plus_position]
            self._suffix = type_part_remainder[plus_position:]
        else:
            self._subtype = type_part_remainder
            self._suffix = None
        self._extensions = extensions if extensions else ()

    @override
    def __hash__(self) -> int:
        return hash(self._str)

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
    def subtypes(self) -> Sequence[str]:
        """
        The subtype parts, e.g. ``["vnd", "oasis", "opendocument", "text"]`` for ``"application/vnd.oasis.opendocument.text"``.
        """
        return self._subtype.split("+")[0].split(".")

    @property
    def suffix(self) -> str | None:
        """
        The suffix, e.g. ``json`` for ``application/ld+json``.
        """
        return self._suffix

    @property
    def parameters(self) -> Mapping[str, str]:
        """
        The parameters, e.g. ``{"charset": "UTF-8"}`` for ``"text/html; charset=UTF-8"``.
        """
        return self._parameters

    @property
    def extensions(self) -> Sequence[str]:
        """
        The file extensions associated with this media type.

        Extensions must include a leading dot, and are returned in order of decreasing priority.
        """
        return self._extensions

    @override
    def __str__(self) -> str:
        return self._str

    @override
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, MediaType):
            return NotImplemented
        return (self.type, self.subtype, self.suffix, self.parameters) == (
            other.type,
            other.subtype,
            self.suffix,
            other.parameters,
        )


ExtensionIndicator: TypeAlias = Path | str
"""
A file path or name that includes a file extension.
"""


MediaTypeIndicator: TypeAlias = MediaType | ExtensionIndicator
"""
A media type, or a file path or name that indicates a media type through its file extension.
"""


@final
class MediaTypeSchema(Singleton, String):
    """
    A JSON Schema for :py:class:`betty.media_type.MediaType`.
    """

    def __init__(self):
        super().__init__(
            def_name="mediaType",
            title="Media type",
            description="An IANA media type (https://www.iana.org/assignments/media-types/media-types.xhtml).",
        )


def match_media_type(source: MediaType, media_types: Iterable[MediaType]) -> MediaType:
    """
    Match a media type against available media types.
    """
    for media_type in media_types:
        if source == media_type:
            return media_type
    raise UnsupportedMediaType(source)


def match_extension(
    source: ExtensionIndicator, media_types: Iterable[MediaType]
) -> tuple[MediaType, str]:
    """
    Match a file extension indicator against available media types.
    """
    if isinstance(source, Path):
        return match_extension(source.name, media_types)
    for media_type in media_types:
        for extension in media_type.extensions:
            if source.endswith(extension):
                return media_type, extension
    raise UnsupportedMediaType(source)
