"""
Provide `media type <https://en.wikipedia.org/wiki/Media_type>`_ handling utilities.
"""

from __future__ import annotations

from email.message import EmailMessage
from typing import TYPE_CHECKING, Final, Self, final, override

from betty.assertions.str import assert_str
from betty.data import Data, DataDefinition
from betty.definition.human_facing import HumanFacingDefinition
from betty.localizables.gettext import _, ngettext
from betty.pathlib import StrPath
from betty.plugin import PluginTypeDefinition
from betty.plugin.ordered import Order, OrderedPluginDefinition
from betty.portable import Portable, PortableData

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence

    from betty.localizable import ResolvableLocalizable
    from betty.machine_name import ResolvableMachineName


class InvalidMediaType(ValueError):
    """
    Raised when an identifier is not a valid media type.
    """


class UnsupportedMediaType(RuntimeError):
    """
    Raised when a media type is not supported.
    """

    def __init__(self, media_type: MediaTypeIndicator, /):
        super().__init__(f"Unsupported media type: {media_type}")


class MissingMediaType(RuntimeError):
    """
    Raised when a media type is not missing.
    """

    def __init__(self):
        super().__init__("Missing media type")


@final
@DataDefinition(label=_("Media type"))
class MediaType(Data, Portable):
    """
    Define a `media type <https://en.wikipedia.org/wiki/Media_type>`_.

    Media types are also commonly known as content types or MIME types.
    """

    _suffix: str | None

    def __init__(self, media_type: str, *, extensions: Sequence[str] = ()):
        self._str = media_type
        message = EmailMessage()
        message["Content-Type"] = media_type
        type_part = message.get_content_type()
        # EmailMessage.get_content_type() always returns a type, and will fall back to alternatives if the header is
        # invalid.
        if not media_type.startswith(type_part):
            raise InvalidMediaType(f'"{media_type}" is not a valid media type.')
        self.parameters: Mapping[str, str] = dict(message["Content-Type"].params)
        """
        The parameters, e.g. ``{"charset": "UTF-8"}`` for ``"text/html; charset=UTF-8"``.
        """
        _type, type_part_remainder = type_part.split("/")
        self.type: Final[str] = _type
        """
        The type, e.g. ``application`` for ``application/ld+json``.
        """
        if not type_part_remainder:
            raise InvalidMediaType("The subtype must not be empty.")
        plus_position = type_part_remainder.find("+")
        if plus_position > 0:
            subtype = type_part_remainder[0:plus_position]
            suffix = type_part_remainder[plus_position:]
        else:
            subtype = type_part_remainder
            suffix = None
        self.subtype: Final[str] = subtype
        """
        The subtype, e.g. ``"vnd.oasis.opendocument.text"`` for ``"application/vnd.oasis.opendocument.text"``.
        """
        self.subtypes = subtype.split("+")[0].split(".")
        """
        The subtype parts, e.g. ``["vnd", "oasis", "opendocument", "text"]`` for ``"application/vnd.oasis.opendocument.text"``.
        """
        self.suffix: Final[str | None] = suffix
        """
        The suffix, e.g. ``json`` for ``application/ld+json``.
        """
        self.extensions: Sequence[str] = extensions
        """
        The file extensions associated with this media type.

        Extensions must include a leading dot, and are returned in order of decreasing priority.
        """

    @override
    def __hash__(self) -> int:
        return hash(self._str)

    @override
    def __str__(self) -> str:
        return self._str

    @override
    def __eq__(self, other: object) -> bool:
        if isinstance(other, str):
            try:
                return self == MediaType(other)
            except InvalidMediaType:
                return False
        if not isinstance(other, MediaType):
            return NotImplemented
        return (self.type, self.subtype, self.suffix, self.parameters) == (
            other.type,
            other.subtype,
            self.suffix,
            other.parameters,
        )

    @override
    @classmethod
    def load(cls, portable: PortableData, /) -> Self:
        return cls(assert_str()(portable))

    @override
    def dump(self) -> PortableData:
        return self._str


type MediaTypeIndicator = MediaType | StrPath
"""
A media type, or a file path or name that indicates a media type through its file extension.
"""


def match_media_type(
    match: MediaType, supported_media_types: Iterable[MediaType], /
) -> MediaType:
    """
    Match a media type against available media types.
    """
    for supported_media_type in supported_media_types:
        if supported_media_type == match:
            return supported_media_type
    raise UnsupportedMediaType(match)


def match_extension(
    match: StrPath, supported_media_types: Iterable[MediaType], /
) -> tuple[MediaType, str]:
    """
    Match a file extension indicator against available media types.
    """
    match = str(match)
    for supported_media_type in supported_media_types:
        for extension in supported_media_type.extensions:
            if match.endswith(extension):
                return supported_media_type, extension
    raise UnsupportedMediaType(match)


@final
@PluginTypeDefinition(
    "media-type",
    label=_("Media type"),
    label_plural=_("Media types"),
    label_countable=ngettext("{count} media type", "{count} media types"),
)
class MediaTypeDefinition(HumanFacingDefinition, OrderedPluginDefinition):
    """
    .. plugin_type:: media-type.
    """

    def __init__(
        self,
        plugin_id: ResolvableMachineName,
        *,
        label: ResolvableLocalizable,
        description: ResolvableLocalizable | None = None,
        media_type: MediaType,
        after: Order[MediaTypeDefinition] = (),
        auto: bool = True,
        before: Order[MediaTypeDefinition] = (),
    ):
        super().__init__(
            plugin_id,
            after=after,
            auto=auto,
            before=before,
            description=description,
            label=label,
        )
        self._media_type = media_type

    @override
    def __eq__(self, other: object) -> bool:
        if isinstance(other, MediaType):
            return self.media_type == other
        if not isinstance(other, MediaTypeDefinition):
            return NotImplemented
        return self.id == other.id and self.media_type == other.media_type

    @property
    def media_type(self) -> MediaType:
        """
        The media type.
        """
        return self._media_type


type ResolvableMediaType = MediaType | MediaTypeDefinition


def resolve_media_type(media_type: ResolvableMediaType, /) -> MediaType:
    """
    Resolve a media type.
    """
    if isinstance(media_type, MediaType):
        return media_type
    return media_type.media_type
