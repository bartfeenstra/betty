"""
Content types.
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from collections.abc import Callable, Iterable, Iterator, Sequence
from typing import TYPE_CHECKING, Final, Self, final, override

from betty.definition.human_facing import HumanFacingDefinition
from betty.definition.ordered import Order, OrderedDefinition
from betty.exception import HumanFacingException
from betty.localizables.gettext import _, ngettext
from betty.localizables.markup import Paragraph, do_you_mean
from betty.media_type import MediaType, ResolvableMediaType
from betty.pathlib import Extension, ResolvableExtension, StrPath
from betty.plugin import PluginDefinition, PluginTypeDefinition
from betty.typing import RuntimeCheckableSequence, is_runtime_checkable_sequence

if TYPE_CHECKING:
    from ty_extensions import Intersection

    from betty.localizer import AnyLocalizable
    from betty.machine_name import ResolvableMachineName

type ContentTypeDefinitionExtension = (
    ResolvableExtension | RuntimeCheckableSequence[ResolvableExtension]
)
type ContentTypeDefinitionMediaType = (
    ResolvableMediaType | RuntimeCheckableSequence[ResolvableMediaType]
)


class _ContentTypeNegotiationError(HumanFacingException, ValueError):
    pass


@final
class UnsupportedContentType(_ContentTypeNegotiationError):
    """
    Raised when a content type is not supported.
    """

    _message = _("Unsupported content type.")

    def __init__(self, *content_types: ContentTypeDefinition):
        super().__init__(
            Paragraph(
                self._message,
                do_you_mean(
                    *(content_type.definition.label for content_type in content_types)
                ),
            )
        )


@final
class UnsupportedMediaType(_ContentTypeNegotiationError):
    """
    Raised when a media type is not supported.
    """

    _message = _("Unsupported media type.")

    def __init__(self, *content_types: ContentTypeDefinition):
        super().__init__(
            Paragraph(
                self._message,
                do_you_mean(
                    *(
                        _("{media_type} ({content_type})").format(
                            media_type=media_type,
                            content_type=content_type.definition.label,
                        )
                        for content_type in content_types
                        for media_type in content_type.media_types
                    )
                ),
            )
        )


@final
class UnsupportedExtension(_ContentTypeNegotiationError):
    """
    Raised when a file extension is not supported.
    """

    _message = _("Unsupported file type.")

    def __init__(self, *content_types: ContentTypeDefinition):
        super().__init__(
            Paragraph(
                self._message,
                do_you_mean(
                    *(
                        _("{extension} ({content_type})").format(
                            extension=extension,
                            content_type=content_type.definition.label,
                        )
                        for content_type in content_types
                        for extension in content_type.extensions
                    )
                ),
            )
        )


@final
class MissingContentType(RuntimeError):
    """
    Raised when a content type is missing.
    """

    def __init__(self):
        super().__init__("Missing content type")


@final
class MissingMediaType(RuntimeError):
    """
    Raised when a content type's media type is missing.
    """

    def __init__(self, content_type: ContentTypeDefinition, /):
        super().__init__(
            f'Content type "{content_type.id}" does not have any associated media types.'
        )


@final
class MissingExtension(RuntimeError):
    """
    Raised when a content type's extension is missing.
    """

    def __init__(self, content_type: ContentTypeDefinition, /):
        super().__init__(
            f'Content type "{content_type.id}" does not have any associated file extensions.'
        )


class _Negotiator[MatchableT, MatchT](metaclass=ABCMeta):
    __slots__ = ()

    @abstractmethod
    def request(self, other: MatchableT | None, /) -> MatchT | None:
        """
        Request a match by a content type indicator.
        """

    @final
    def require(self, other: MatchableT | None, /) -> MatchT:
        """
        Require a match by a content type indicator.
        """
        if match := self.request(other):
            return match
        # @todo We have 3(!) error classes now, depending on what details calling code needs.
        # @todo Maybe we need an implementation on
        # @todo - ContentTypeNegotiator
        # @todo - MediaTypeNegotiator
        # @todo - ExtensionNegotiator
        # @todo to ensure we raise the right exceptions everywhere?
        # @todo OOOOH! Create 3 little mixins.
        # @todo
        raise UnsupportedContentType(other)


type MediaTypeNegotiator = Intersection[
    _Negotiator[
        ContentTypeDefinition | ResolvableMediaType,
        tuple[ContentTypeDefinition, MediaType],
    ],
    Iterable[MediaType],
]


type ExtensionNegotiator = Intersection[
    _Negotiator[
        ContentTypeDefinition | ResolvableExtension,
        tuple[ContentTypeDefinition, Extension],
    ],
    Iterable[Extension],
]


class ContentTypeNegotiator(
    _Negotiator[
        "ContentTypeDefinition | ResolvableMediaType | ResolvableExtension",
        "ContentTypeDefinition",
    ]
):
    """
    A content type negotiator.
    """

    __slots__ = ()

    @property
    @abstractmethod
    def media_types(self) -> MediaTypeNegotiator:
        """
        Match by file extensions.
        """

    @property
    @abstractmethod
    def extensions(self) -> ExtensionNegotiator:
        """
        Match by file extensions.
        """


@final
class _ContentTypeDefinitionExtensionNegotiator(
    _Negotiator[
        "ContentTypeDefinition | ResolvableExtension",
        tuple["ContentTypeDefinition, Extension"],
    ]
):
    __slots__ = ("_content_type", "_extensions")

    def __init__(self, content_type: ContentTypeDefinition, *extensions: Extension):
        self._extensions = set(extensions)
        self._content_type = content_type

    def __iter__(self) -> Iterator[Extension]:
        return self._extensions.__iter__()

    @override
    def request(
        self, other: StrPath | None, /
    ) -> tuple[ContentTypeDefinition, Extension] | None:
        if other is None:
            return None
        other = Extension(other)
        if other in self._extensions:
            return self._content_type, other
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
            "A content type must have at least one media type or extension."
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
        try:
            return next(iter(self.media_types))
        except StopIteration:
            raise MissingMediaType(self) from None

    @property
    def extension(self) -> Extension:
        """
        The preferred file extension, if any.
        """
        try:
            return next(iter(self.extensions))
        except StopIteration:
            raise MissingExtension(self) from None

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
    __slots__ = ("_extensions",)

    def __init__(self, *content_types: ContentTypeDefinition):
        self._extensions = {
            extension: content_type
            for content_type in reversed(content_types)
            for extension in content_type.extensions
        }

    def __iter__(self) -> Iterator[Extension]:
        yield from self._extensions

    @override
    def request(
        self, other: StrPath | None, /
    ) -> tuple[ContentTypeDefinition, Extension] | None:
        if other is None:
            return None
        other = Extension(other)
        match = self._extensions.get(other, None)
        if match:
            return match, other
        return None


# @todo Develop this further.
# @todo We have 2 input types:
# @todo - ContentTypeDefinition (must provide the keys, because the necessary key data does not exist on the definition yet)
# @todo - ContentTypeRepository (the definitions are complete and we can key anything we'd like)
# @todo And 3 output types (each with their own .require() mixin):
# @todo - ContentTypeDefinition
# @todo - tuple[ContentTypeDefinition, MediaType]
# @todo - tuple[ContentTypeDefinition, Extension]
# @todo
# @todo
# @todo
@final
class _MappingNegotiator[MatchableT, MatchT, KeyT](_Negotiator[MatchableT, MatchT]):
    __slots__ = ("_content_types", "_resolver")

    def __init__(
        self,
        keyer: Callable[[ContentTypeDefinition], Iterable[KeyT]],
        resolver: Callable[[MatchableT], KeyT],
        *content_types: ContentTypeDefinition,
    ):
        self._content_types = {
            key: content_type
            for content_type in reversed(content_types)
            for key in keyer(content_type)
        }
        self._resolver = resolver

    def __iter__(self) -> Iterator[KeyT]:
        yield from self._content_types

    @override
    def request(
        self, other: StrPath | None, /
    ) -> tuple[ContentTypeDefinition, Extension] | None:
        if other is None:
            return None
        other = self._resolver(other)
        match = self._content_types.get(other, None)
        if match:
            return match, other
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
