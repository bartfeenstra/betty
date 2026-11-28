"""
Content types.
"""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Collection
from typing import TYPE_CHECKING, Self, final, override

from ty_extensions import Not

from betty.definition.human_facing import HumanFacingDefinition
from betty.definition.id import ResolvableId, resolve_id
from betty.definition.ordered import Order, OrderedDefinition
from betty.exception import HumanFacingException
from betty.localizables.gettext import _, ngettext
from betty.localizables.markup import Paragraphs, Quote, do_you_mean
from betty.machine_name import MachineName
from betty.media_type import MediaType, ResolvableMediaType
from betty.negotiation import MappingNegotiator, Negotiator
from betty.pathlib import Extension, ResolvableExtension
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


class _UnsupportedContentTypeIndicator(HumanFacingException, ValueError):
    pass


@final
class UnsupportedContentType(_UnsupportedContentTypeIndicator):
    """
    Raised when a content type is not supported.
    """

    def __init__(self, value: MachineName, *content_types: ContentTypeDefinition):
        super().__init__(
            Paragraphs(
                _("Unsupported content type {value}.").format(value=Quote(value)),
                do_you_mean(
                    *(content_type.definition.label for content_type in content_types)
                ),
            )
        )


@final
class UnsupportedMediaType(_UnsupportedContentTypeIndicator):
    """
    Raised when a media type is not supported.
    """

    def __init__(self, value: ResolvableMediaType, *media_types: MediaType):
        super().__init__(
            Paragraphs(
                _("Unsupported media type {value}.").format(value=Quote(value)),
                do_you_mean(*media_types),
            )
        )


@final
class UnsupportedExtension(_UnsupportedContentTypeIndicator):
    """
    Raised when a file extension is not supported.
    """

    def __init__(self, value: ResolvableExtension, *extensions: Extension):
        super().__init__(
            Paragraphs(
                _("Unsupported file type {value}.").format(value=Quote(str(value))),
                do_you_mean(*extensions),
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

    def __init__(self, content_type: ContentTypeDefinition | None = None, /):
        super().__init__(
            f'Content type "{content_type.id}" does not have any associated media types.'
            if content_type
            else "No media type was given."
        )


@final
class MissingExtension(RuntimeError):
    """
    Raised when a content type's extension is missing.
    """

    def __init__(self, content_type: ContentTypeDefinition | None = None, /):
        super().__init__(
            f'Content type "{content_type.id}" does not have any associated file extensions.'
            if content_type
            else "No extension was given."
        )


class MediaTypeNegotiator(
    Negotiator[
        MediaType,
        ResolvableMediaType,
        tuple["ContentTypeDefinition", MediaType],
        UnsupportedMediaType | MissingMediaType,
    ],
    Collection[MediaType],
):
    """
    Negotiate content types by media type.
    """

    __slots__ = ()

    @final
    @override
    def _new_unsupported(
        self, other: ResolvableMediaType, /
    ) -> UnsupportedMediaType | MissingMediaType:
        return UnsupportedMediaType(other, *self)


class ExtensionNegotiator(
    Negotiator[
        Extension,
        ResolvableExtension,
        tuple["ContentTypeDefinition", Extension],
        UnsupportedExtension | MissingMediaType,
    ],
    Collection[Extension],
):
    """
    Negotiate content types by file extension.
    """

    __slots__ = ()

    @final
    @override
    def _new_unsupported(
        self, other: ResolvableExtension, /
    ) -> UnsupportedExtension | MissingMediaType:
        return UnsupportedExtension(other, *self)


class ContentTypeNegotiator(
    Negotiator[
        MachineName,
        "ResolvableId[ContentTypeDefinition] | None",
        "ContentTypeDefinition",
        UnsupportedContentType | MissingMediaType,
    ]
):
    """
    Negotiate content types.
    """

    __slots__ = ()

    @property
    @abstractmethod
    def media_types(self) -> MediaTypeNegotiator:
        """
        Match by associated media types.
        """

    @property
    @abstractmethod
    def extensions(self) -> ExtensionNegotiator:
        """
        Match by associated file extensions.

        Extensions include a leading dot, and are ordered by decreasing priority.
        """


class _CollectionMappingNegotiator[
    KeyT,
    ResolvableKeyT,
    MatchT: Not[None],
    UnsupportedT: Exception,
    ValueT,
](
    MappingNegotiator[KeyT, ResolvableKeyT, MatchT, UnsupportedT, ValueT],
    Collection[ValueT],
):
    def __contains__(self, key: ResolvableKeyT | KeyT):
        return self._resolve(key) in self._values

    def __iter__(self):
        return self._values.__iter__()

    def __len__(self):
        return self._values.__len__()


@final
class _MediaTypeMappingNegotiator(
    _CollectionMappingNegotiator[
        MediaType,
        ResolvableMediaType,
        tuple["ContentTypeDefinition", MediaType],
        UnsupportedMediaType | MissingMediaType,
        MediaType,
    ],
    MediaTypeNegotiator,
):
    pass


@final
class _ExtensionMappingNegotiator(
    _CollectionMappingNegotiator[
        Extension,
        ResolvableExtension,
        tuple["ContentTypeDefinition", Extension],
        UnsupportedExtension | MissingMediaType,
        Extension,
    ],
    ExtensionNegotiator,
):
    pass


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
        self._media_types = _MediaTypeMappingNegotiator(self)
        self._extensions = _ExtensionMappingNegotiator(self)

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

    @final
    @override
    def _new_unsupported(
        self, other: ResolvableId[ContentTypeDefinition] | None, /
    ) -> UnsupportedContentType | MissingMediaType:
        if other is None:
            return MissingMediaType()
        return UnsupportedContentType(resolve_id(other), self)

    @override
    def request(
        self, other: ResolvableId[ContentTypeDefinition] | None, /
    ) -> ContentTypeDefinition | None:
        if other is None:
            return None
        if resolve_id(other) == self.id:
            return self
        return None

    @override
    @property
    def media_types(self) -> MediaTypeNegotiator:
        return self._media_types

    @override
    @property
    def extensions(self) -> ExtensionNegotiator:
        return self._extensions


@final
class ContentTypeRepository(
    _CollectionMappingNegotiator[
        MachineName,
        ResolvableId[ContentTypeDefinition] | None,
        ContentTypeDefinition,
        UnsupportedContentType | MissingMediaType,
        Extension,
    ],
    ContentTypeNegotiator,
):
    """
    A sequence of content types that can be matched against.
    """

    def __init__(self, *content_types: ContentTypeDefinition):
        self._content_types = {
            content_type.id: content_type for content_type in content_types
        }
        self._media_types = _MediaTypeMappingNegotiator(self)
        self._extensions = _ExtensionMappingNegotiator(self)

    def __iter__(self):
        yield from self._content_types.values()

    @override
    def _new_unsupported(
        self, other: ResolvableId[ContentTypeDefinition] | None, /
    ) -> UnsupportedContentType | MissingMediaType:
        if other is None:
            return MissingMediaType()
        return UnsupportedContentType(resolve_id(other), *self)

    @override
    @property
    def media_types(self) -> MediaTypeNegotiator:
        return self._media_types

    @override
    @property
    def extensions(self) -> ExtensionNegotiator:
        return self._extensions
