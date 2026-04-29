"""
Provide `media type <https://en.wikipedia.org/wiki/Media_type>`_ handling utilities.
"""

from __future__ import annotations

from email.message import EmailMessage
from typing import TYPE_CHECKING, Self, final, override

from betty.assertion import assert_str
from betty.data import Data, DataDefinition
from betty.definition.human_facing import HumanFacingDefinition
from betty.locale.localizable.gettext import _, ngettext
from betty.pathlib import StrPath
from betty.plugin import PluginTypeDefinition
from betty.plugin.ordered import Order, OrderedPluginDefinition
from betty.portable import Portable, PortableData
from betty.property import Property

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Mapping, Sequence

    from betty.locale.localizable import ResolvableLocalizable
    from betty.machine_name import ResolvableMachineName


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
        self._extensions = extensions

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
    def __eq__(self, other: object) -> bool:
        if isinstance(other, MediaTypeDefinition):
            return self == other.media_type
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


def match_media_type(source: MediaType, media_types: Iterable[MediaType]) -> MediaType:
    """
    Match a media type against available media types.
    """
    for media_type in media_types:
        if source == media_type:
            return media_type
    raise UnsupportedMediaType(source)


def match_extension(
    source: StrPath, media_types: Iterable[MediaType], /
) -> tuple[MediaType, str]:
    """
    Match a file extension indicator against available media types.
    """
    source = str(source)
    for media_type in media_types:
        for extension in media_type.extensions:
            if source.endswith(extension):
                return media_type, extension
    raise UnsupportedMediaType(source)


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

    @property
    def media_type(self) -> MediaType:
        """
        The media type.
        """
        return self._media_type


type ResolvableMediaType = MediaType | MediaTypeDefinition


@final
class MediaTypeProperty(Property[MediaType, ResolvableMediaType]):
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


def resolve_media_type(media_type: ResolvableMediaType, /) -> MediaType:
    """
    Resolve a media type.
    """
    if isinstance(media_type, MediaType):
        return media_type
    return media_type.media_type
