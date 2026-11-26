"""
Content types.
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from collections.abc import Iterable, Iterator, Sequence
from typing import TYPE_CHECKING, Final, Self, final, override

from betty.definition.human_facing import HumanFacingDefinition
from betty.definition.ordered import Order, OrderedDefinition
from betty.localizables.gettext import _, ngettext
from betty.media_type import MediaType, ResolvableMediaType, UnsupportedMediaType
from betty.pathlib import Extension, ResolvableExtension, StrPath
from betty.plugin import PluginDefinition, PluginTypeDefinition
from betty.typing import RuntimeCheckableSequence, is_runtime_checkable_sequence

if TYPE_CHECKING:
    from betty.localizer import AnyLocalizable
    from betty.machine_name import ResolvableMachineName

type ContentTypeDefinitionExtension = (
    ResolvableExtension | RuntimeCheckableSequence[ResolvableExtension]
)
type ContentTypeDefinitionMediaType = (
    ResolvableMediaType | RuntimeCheckableSequence[ResolvableMediaType]
)


class _ContentTypeNegotiator[MatchableT, MatchT](metaclass=ABCMeta):
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


class MediaTypeNegotiator(
    _ContentTypeNegotiator[
        "ResolvableMediaType | ContentTypeDefinition", "ContentTypeDefinition"
    ]
):
    """
    A content type media type negotiator.
    """

    __slots__ = ()


class ExtensionNegotiator(
    _ContentTypeNegotiator[StrPath, tuple["ContentTypeDefinition", Extension]],
    Iterable[Extension],
):
    """
    A content type file extension negotiator.
    """

    __slots__ = ()


class ContentTypeNegotiator(MediaTypeNegotiator):
    """
    A content type negotiator.
    """

    __slots__ = ()

    # @todo This allows calling code to know exactly which extension was matched on.
    # @todo Do we need a variant that instead of (ContentTypeDefinition, str) returns (ContentTypeDefinition, MediaType)?
    @property
    @abstractmethod
    def extensions(self) -> ExtensionNegotiator:
        """
        Match by file extensions.
        """


@final
class _ContentTypeDefinitionExtensionNegotiator(ExtensionNegotiator):
    __slots__ = ("_extensions", "_media_type")

    def __init__(self, media_type: ContentTypeDefinition, *extensions: Extension):
        self._extensions = extensions
        self._media_type = media_type

    def __iter__(self) -> Iterator[Extension]:
        return self._extensions.__iter__()

    @override
    def request(
        self, other: StrPath | None, /
    ) -> tuple[ContentTypeDefinition, Extension] | None:
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
    "content-type",
    label=_("Content type"),
    label_plural=_("Content types"),
    label_countable=ngettext("{count} content type", "{count} content types"),
)
class ContentTypeDefinition(
    HumanFacingDefinition, OrderedDefinition, PluginDefinition, ContentTypeNegotiator
):
    """
    .. plugin_type:: content-type.
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
        extension: ContentTypeDefinitionExtension = (),
        label: AnyLocalizable,
        media_type: ContentTypeDefinitionMediaType = (),
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

        self._extensions = _ContentTypeDefinitionExtensionNegotiator(
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
        self, other: ResolvableMediaType | ContentTypeDefinition | None, /
    ) -> ContentTypeDefinition | None:
        if other is None:
            return None
        if isinstance(other, ContentTypeDefinition):
            if other is self:
                return self
            return None
        for media_type in self.media_types:
            if media_type.match(other):
                return self
        return None

    @override
    @property
    def extensions(self) -> ExtensionNegotiator:
        """
        The associated file extensions.

        Extensions include a leading dot, and are ordered by decreasing priority.
        """
        return self._extensions


@final
class _ContentTypeRepositoryExtensionNegotiator(ExtensionNegotiator):
    __slots__ = ("_media_types",)

    def __init__(self, media_types: Iterable[ContentTypeDefinition]):
        self._media_types = media_types

    def __iter__(self) -> Iterator[Extension]:
        for media_type in self._media_types:
            yield from media_type.extensions

    @override
    def request(
        self, other: StrPath | None, /
    ) -> tuple[ContentTypeDefinition, Extension] | None:
        if other is None:
            return None
        other = Extension(other)
        # @todo Add caching here, now we have normalized ``other``
        for media_type in self._media_types:
            if match := media_type.extensions.request(other):
                return match
        return None


@final
class ContentTypeRepository(ContentTypeNegotiator):
    """
    A sequence of content types that can be matched against.
    """

    __slots__ = ("_extensions", "_media_types")

    def __init__(self, *media_types: ContentTypeDefinition):
        self._media_types = media_types
        self._extensions = _ContentTypeRepositoryExtensionNegotiator(self)

    def __iter__(self):
        return self._media_types.__iter__()

    @override
    def request(
        self, other: ResolvableMediaType | ContentTypeDefinition | None, /
    ) -> ContentTypeDefinition | None:
        if other is None:
            return None
        for media_type in self._media_types:
            if media_type.request(other):
                return media_type
        return None

    @override
    @property
    def extensions(self) -> ExtensionNegotiator:
        return self._extensions
