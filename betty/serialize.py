"""
The (de)serialization API.
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Final, final

from betty.definition import HasDefinition
from betty.definition.cls import ClsDefinition
from betty.definition.human_facing import HumanFacingDefinition
from betty.exception import HumanFacingException
from betty.localizables.gettext import _, ngettext
from betty.localizables.markup import JoinOr, Quote
from betty.plugin import PluginDefinition, PluginTypeDefinition

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.content_type import ContentTypeDefinition
    from betty.localizer import AnyLocalizable
    from betty.machine_name import ResolvableMachineName
    from betty.pathlib import StrPath
    from betty.portable import PortableData
    from betty.requirement import Requires


class SerializationError(HumanFacingException):
    """
    Raised when an error occurs during (de)serialization.
    """


class Serializer(HasDefinition["SerializerDefinition"], metaclass=ABCMeta):
    """
    A serializer.
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
class SerializerDefinition(
    HumanFacingDefinition, ClsDefinition[Serializer], PluginDefinition
):
    """
    .. plugin_type:: serializer.
    """

    def __init__(
        self,
        id_: ResolvableMachineName,
        content_type: ContentTypeDefinition,
        /,
        *,
        label: AnyLocalizable,
        auto: bool = True,
        description: AnyLocalizable | None = None,
        requires: Requires = (),
    ):
        super().__init__(
            id_, auto=auto, label=label, description=description, requires=requires
        )
        self.content_type: Final[ContentTypeDefinition] = content_type


# @todo Refactor this around ContentTypeNegotiator?
def serializer_for(
    available_serializers: Iterable[Serializer], extension: StrPath, /
) -> Serializer:
    """
    Get the serializer for the given file extension.
    """
    for available_serializer in available_serializers:
        if available_serializer.definition.content_type.extensions.request(extension):
            return available_serializer
    raise SerializationError(
        _("Unsupported file {unsupported}. Supported types are: {supported}.").format(
            unsupported=Quote(str(extension)),
            supported=JoinOr(*[
                _("{content_type} ({extensions})").format(
                    content_type=available_serializer.definition.content_type.label,
                    extensions=JoinOr(
                        *available_serializer.definition.content_type.extensions
                    ),
                )
                for available_serializer in available_serializers
            ]),
        )
    )
