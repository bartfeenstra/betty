"""
The (de)serialization API.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, final

from betty.definition.human_facing import HumanFacingDefinition
from betty.exception import HumanFacingException
from betty.localizables.gettext import _, ngettext
from betty.localizables.markup import JoinOr, Quote
from betty.localizables.plain import Plain
from betty.plugin import PluginTypeDefinition
from betty.plugin.cls import Plugin, PluginClsDefinition

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.localizable import ResolvableLocalizable
    from betty.machine_name import ResolvableMachineName
    from betty.media_type import MediaType
    from betty.portable import PortableData
    from betty.requirement import Requires


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
class SerializerDefinition(HumanFacingDefinition, PluginClsDefinition[Serializer]):
    """
    .. plugin_type:: serializer.
    """

    def __init__(
        self,
        plugin_id: ResolvableMachineName,
        *,
        label: ResolvableLocalizable,
        auto: bool = True,
        description: ResolvableLocalizable | None = None,
        requires: Requires = (),
    ):
        super().__init__(
            plugin_id,
            auto=auto,
            label=label,
            description=description,
            requires=requires,
        )


def serializer_for(
    available_serializers: Iterable[Serializer], extension: str, /
) -> Serializer:
    """
    Get the serializer for the given file extension.
    """
    for available_serializer in available_serializers:
        if extension in available_serializer.media_type().extensions:
            return available_serializer
    raise SerializationError(
        _("Unsupported file {unsupported}. Supported types are: {supported}.").format(
            unsupported=Quote(extension),
            supported=JoinOr(*[
                Plain("{extension} ({available_type})").format(
                    extension=extension,
                    available_type=available_serializer.plugin().label,
                )
                for available_serializer in available_serializers
                for extension in available_serializer.media_type().extensions
            ]),
        )
    )
