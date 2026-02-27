"""
The (de)serialization API.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, final

from betty.definition.human_facing import HumanFacingDefinition
from betty.exception import HumanFacingException
from betty.locale.localizable.gettext import _, ngettext
from betty.locale.localizable.markup import AnyEnumeration
from betty.locale.localizable.plain import Plain
from betty.plugin import Plugin, PluginDefinition, PluginTypeDefinition

if TYPE_CHECKING:
    from collections.abc import Sequence

    from betty.media_type import MediaType
    from betty.portable import PortableData


class SerializationError(HumanFacingException):
    """
    Raised when an error occurs during (de)serialization.
    """


class Serializer(ABC, Plugin["SerializerDefinition"]):
    """
    A serializer.
    """

    @classmethod
    @abstractmethod
    def media_type(cls) -> MediaType:
        """
        The media type this serializer can serialize.
        """

    @abstractmethod
    def load(self, serialized: str, /) -> PortableData:
        """
        Deserialize data.

        :raise SerializationError: Raised when the dump could not be loaded.
        """

    @abstractmethod
    def dump(self, portable: PortableData, /) -> str:
        """
        Serialize data.
        """


@final
@PluginTypeDefinition(
    "serializer",
    label=_("Serializer"),
    label_plural=_("Serializers"),
    label_countable=ngettext("{count} serializer", "{count} serializers"),
)
class SerializerDefinition(HumanFacingDefinition, PluginDefinition[Serializer]):
    """
    .. plugin_type:: serializer.
    """


def serializer_for(
    available_serializers: Sequence[SerializerDefinition], extension: str, /
) -> SerializerDefinition:
    """
    Get the serializer for the given file extension.
    """
    for available_serializer in available_serializers:
        if extension in available_serializer.cls.media_type().extensions:
            return available_serializer
    raise SerializationError(
        _(
            'Unsupported file "{unsupported_type}". Supported types are: {available_types}.'
        ).format(
            unsupported_type=extension,
            available_types=AnyEnumeration(
                *[
                    Plain("{extension} ({available_type})").format(
                        extension=extension, available_type=available_serializer.label
                    )
                    for available_serializer in available_serializers
                    for extension in available_serializer.cls.media_type().extensions
                ]
            ),
        )
    )
