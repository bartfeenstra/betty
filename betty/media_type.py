"""
Provide `media type <https://en.wikipedia.org/wiki/Media_type>`_ handling utilities.
"""

from __future__ import annotations

from email.message import EmailMessage
from enum import StrEnum, auto
from typing import TYPE_CHECKING, Any, final, override

from betty.assertions.str import assert_str
from betty.collections.mapping.dict import FrozenDict, empty_frozen_dict
from betty.data import Data, DataDefinition
from betty.freezers.frozen import Frozen
from betty.localizables.gettext import _
from betty.localizables.markup import do_you_mean
from betty.localizer import default_localizer
from betty.pipeline import pipe
from betty.porters.callback import CallbackPorter
from betty.sample import Sample

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence


type ResolvableMediaType = MediaType | str
"""
A value that can be resolved to a :py:class:`betty.media_type.MediaType`.
"""


class InvalidMediaType(ValueError):
    """
    Raised when an identifier is not a valid media type.
    """


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
        message_params = message["Content-Type"].params
        parameters = FrozenDict(message_params) if message_params else empty_frozen_dict
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
