"""
Provide `media type <https://en.wikipedia.org/wiki/Media_type>`_ handling utilities.
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from collections.abc import Iterable, Iterator
from email.message import EmailMessage
from enum import StrEnum, auto
from typing import TYPE_CHECKING, Any, Final, Self, final, override

from betty.assertions.str import assert_str
from betty.data import Data, DataDefinition
from betty.definition.human_facing import HumanFacingDefinition
from betty.definition.ordered import Order, OrderedDefinition
from betty.freezers.frozen import Frozen
from betty.localizables.gettext import _, ngettext
from betty.localizables.markup import do_you_mean
from betty.localizer import default_localizer
from betty.pathlib import Extension, ResolvableExtension, StrPath
from betty.pipeline import pipe
from betty.plugin import PluginDefinition, PluginTypeDefinition
from betty.porters.callback import CallbackPorter
from betty.sample import Sample
from betty.typing import RuntimeCheckableSequence, is_runtime_checkable_sequence

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from betty.localizer import AnyLocalizable
    from betty.machine_name import ResolvableMachineName


type MediaTypeDefinitionExtension = (
    ResolvableExtension | RuntimeCheckableSequence[ResolvableExtension]
)
type MediaTypeDefinitionMediaType = (
    ResolvableMediaType | RuntimeCheckableSequence[ResolvableMediaType]
)


type ResolvableMediaType = MediaType | str
"""
A value that can be resolved to a :py:class:`betty.media_type.MediaType`.
"""


class InvalidMediaType(ValueError):
    """
    Raised when an identifier is not a valid media type.
    """


class UnsupportedMediaType(RuntimeError):
    """
    Raised when a media type is not supported.
    """

    def __init__(self, media_type: Any, /):
        super().__init__(f"Unsupported media type: {media_type}")


class MissingMediaType(RuntimeError):
    """
    Raised when a media type is not missing.
    """

    def __init__(self):
        super().__init__("Missing media type")


class _MediaTypeMatcher[MatchableT, MatchT](metaclass=ABCMeta):
    __slots__ = ()

    @abstractmethod
    def request(self, other: MatchableT | None, /) -> MatchT | None:
        """
        Request a match by a media type indicator.
        """

    @final
    def require(self, other: MatchableT | None, /) -> MatchT:
        """
        Require a match by a media type indicator.
        """
        if match := self.request(other):
            return match
        raise UnsupportedMediaType(other)


@final
class MediaTypeType(StrEnum):
    """
    A top-level media type.
    """

    APPLICATION = auto()
    AUDIO = auto()
    EXAMPLE = auto()
    FONT = auto()
    HAPTICS = auto()
    IMAGE = auto()
    MESSAGE = auto()
    MODEL = auto()
    MULTIPART = auto()
    TEXT = auto()
    VIDEO = auto()

    # @todo Extract this into a base class in betty.enum? Especially with the upcoming validation PR, that would help
    # @todo make any enum validatable by just subclassing the base class.
    @override
    @classmethod
    def _missing_(cls, value: object) -> Any:
        raise InvalidMediaType(
            f'"{value}" is not a valid top-level media type. '
            + default_localizer.localize(do_you_mean(*sorted(cls)))
        )


@final
@DataDefinition(
    label=_("Media type"),
    porter=lambda _: CallbackPorter(assert_str() | MediaType, pipe),
    samples=Sample(lambda: MediaType("text/plain"), label="Plain text"),
)
class MediaType(Frozen, str, Data):
    """
    Define a `media type <https://en.wikipedia.org/wiki/Media_type>`_.

    Media types are also commonly known as content types or MIME types.
    """

    __slots__ = ("_parameters", "_type", "_subtype", "_subtypes", "_suffix")

    def __new__(  # noqa: D102
        cls, media_type: ResolvableMediaType, /
    ):
        if isinstance(media_type, cls):
            return media_type
        message = EmailMessage()
        message["Content-Type"] = media_type
        # @todo Do we need a new dict? Can we leverage empty_frozen_dict?
        parameters = dict(message["Content-Type"].params)
        type_part = message.get_content_type()
        # EmailMessage.get_content_type() always returns a type, and will fall back to alternatives if the header is
        # invalid.
        if not media_type.startswith(type_part):
            raise InvalidMediaType(f'"{media_type}" is not a valid media type.')
        type_, type_part_remainder = type_part.split("/")
        if not type_part_remainder:
            raise InvalidMediaType("The subtype must not be empty.")
        plus_position = type_part_remainder.find("+")
        if plus_position > 0:
            subtype = type_part_remainder[0:plus_position]
            suffix = type_part_remainder[plus_position:]
        else:
            subtype = type_part_remainder
            suffix = None
        subtypes = subtype.split("+")[0].split(".")
        normalized = type_.lower() + "/" + subtype.lower()
        if suffix:
            normalized += suffix.lower()
        for parameter_name in parameters:
            normalized += f"; {parameter_name.lower()}={parameters[parameter_name]}"
        new = super().__new__(cls, normalized)
        new._parameters = parameters
        new._type = type_
        new._subtype = subtype
        new._subtypes = subtypes
        new._suffix = suffix
        return new

    @property
    def parameters(self) -> Mapping[str, str]:
        """
        The parameters, e.g. ``{"charset": "UTF-8"}`` for ``"text/html; charset=UTF-8"``.
        """
        return self._parameters

    @property
    def type(self) -> MediaTypeType:
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
        return self._subtypes

    @property
    def suffix(self) -> str | None:
        """
        The suffix, e.g. ``json`` for ``application/ld+json``.
        """
        return self._suffix

    def match(self, other: ResolvableMediaType, /) -> bool:
        """
        Check if another media type matches (is compatible with) this one.
        """
        other = MediaType(other)
        return (self.type, self.subtype, self.suffix) == (
            other.type,
            other.subtype,
            other.suffix,
        )


class ExtensionMatcher(
    _MediaTypeMatcher[StrPath, tuple["MediaTypeDefinition", Extension]],
    Iterable[Extension],
):
    """
    A media type file extension matcher.
    """

    __slots__ = ()


class MediaTypeMatcher(
    _MediaTypeMatcher[
        "ResolvableMediaType | MediaTypeDefinition", "MediaTypeDefinition"
    ]
):
    """
    A media type matcher.
    """

    __slots__ = ()

    # @todo This allows calling code to know exactly which extension was matched on.
    # @todo Do we need a variant that instead of (MediaTypeDefinition, str) returns (MediaTypeDefinition, MediaType)?
    @property
    @abstractmethod
    def extensions(self) -> ExtensionMatcher:
        """
        Match by file extensions.
        """


@final
class _MediaTypeDefinitionExtensionMatcher(ExtensionMatcher):
    __slots__ = ("_extensions", "_media_type")

    def __init__(self, media_type: MediaTypeDefinition, *extensions: Extension):
        self._extensions = extensions
        self._media_type = media_type

    def __iter__(self) -> Iterator[Extension]:
        return self._extensions.__iter__()

    @override
    def request(
        self, other: StrPath | None, /
    ) -> tuple[MediaTypeDefinition, Extension] | None:
        if other is None:
            return None
        other = Extension(other)
        # @todo Add caching here, now we have normalized ``other``
        for extension in self._extensions:
            if other == extension:
                return self._media_type, extension
        return None


@final
@PluginTypeDefinition(
    "media-type",
    label=_("Media type"),
    label_plural=_("Media types"),
    label_countable=ngettext("{count} media type", "{count} media types"),
)
class MediaTypeDefinition(
    HumanFacingDefinition, OrderedDefinition, PluginDefinition, MediaTypeMatcher
):
    """
    .. plugin_type:: media-type.
    """

    def __init__(
        self,
        id_: ResolvableMachineName,
        /,
        *,
        after: Order[Self] = (),
        auto: bool = True,
        before: Order[Self] = (),
        description: AnyLocalizable | None = None,
        extension: MediaTypeDefinitionExtension = (),
        label: AnyLocalizable,
        media_type: MediaTypeDefinitionMediaType = (),
    ):
        super().__init__(
            id_,
            after=after,
            auto=auto,
            before=before,
            description=description,
            label=label,
        )
        media_types = tuple(
            map(
                MediaType,
                media_type
                if is_runtime_checkable_sequence(media_type)
                else (media_type,),
            )
        )
        extensions = (
            tuple(extension)
            if is_runtime_checkable_sequence(extension)
            else (extension,)
        )
        assert media_types or extensions, (
            "A media type definition must have at least one media type or extension."
        )
        self.media_types: Final[Sequence[MediaType]] = media_types
        """
        The media types.

        Media types are ordered by decreasing priority.
        """

        self._extensions = _MediaTypeDefinitionExtensionMatcher(
            self, *map(Extension, extensions)
        )

    @property
    def media_type(self) -> MediaType:
        """
        The preferred media type, if any.
        """
        # @todo Raise a custom exception?
        return next(iter(self.media_types))

    @property
    def extension(self) -> Extension:
        """
        The preferred file extension, if any.
        """
        # @todo Raise a custom exception?
        return next(iter(self.extensions))

    @override
    def request(
        self, other: ResolvableMediaType | MediaTypeDefinition | None, /
    ) -> MediaTypeDefinition | None:
        if other is None:
            return None
        if isinstance(other, MediaTypeDefinition):
            if other is self:
                return self
            return None
        for media_type in self.media_types:
            if media_type.match(other):
                return self
        return None

    @override
    @property
    def extensions(self) -> ExtensionMatcher:
        """
        The associated file extensions.

        Extensions include a leading dot, and are ordered by decreasing priority.
        """
        return self._extensions


@final
class _MediaTypeRepositoryExtensionMatcher(ExtensionMatcher):
    __slots__ = ("_media_types",)

    def __init__(self, media_types: Iterable[MediaTypeDefinition]):
        self._media_types = media_types

    def __iter__(self) -> Iterator[Extension]:
        for media_type in self._media_types:
            yield from media_type.extensions

    @override
    def request(
        self, other: StrPath | None, /
    ) -> tuple[MediaTypeDefinition, Extension] | None:
        if other is None:
            return None
        other = Extension(other)
        # @todo Add caching here, now we have normalized ``other``
        for media_type in self._media_types:
            if match := media_type.extensions.request(other):
                return match
        return None


@final
class MediaTypeRepository(MediaTypeMatcher):
    """
    A sequence of media type definitions that can be matched against.
    """

    __slots__ = ("_extensions", "_media_types")

    def __init__(self, *media_types: MediaTypeDefinition):
        self._media_types = media_types
        self._extensions = _MediaTypeRepositoryExtensionMatcher(self)

    def __iter__(self):
        return self._media_types.__iter__()

    @override
    def request(
        self, other: ResolvableMediaType | MediaTypeDefinition | None, /
    ) -> MediaTypeDefinition | None:
        if other is None:
            return None
        for media_type in self._media_types:
            if media_type.request(other):
                return media_type
        return None

    @override
    @property
    def extensions(self) -> ExtensionMatcher:
        return self._extensions
