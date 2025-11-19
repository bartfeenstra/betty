"""
Provide serialization formats.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, ClassVar, final

from typing_extensions import override

from betty.exception import HumanFacingException
from betty.locale.localizable import Localizable, _
from betty.locale.localized import Localized, LocalizedStr
from betty.plugin import (
    ClassedPluginDefinition,
    HumanFacingPluginDefinition,
    PluginTypeDefinition,
)
from betty.plugin.discovery.entry_point import EntryPointDiscovery

if TYPE_CHECKING:
    from collections.abc import Sequence

    from betty.locale.localizer import Localizer
    from betty.media_type import MediaType
    from betty.serde.dump import Dump
    from betty.typing import Voidable


class FormatError(HumanFacingException):
    """
    Raised when data that is being deserialized is provided in an unknown (undeserializable) format.
    """


class Format:
    """
    Defines a (de)serialization format.
    """

    plugin: ClassVar[FormatDefinition]

    @classmethod
    @abstractmethod
    def media_type(cls) -> MediaType:
        """
        The media type this format can (de)serialize.
        """

    @abstractmethod
    def load(self, dump: str) -> Dump:
        """
        Deserialize data.

        :raise FormatError: Raised when the dump could not be loaded.
        """

    @abstractmethod
    def dump(self, dump: Voidable[Dump]) -> str:
        """
        Serialize data.
        """


@final
class FormatDefinition(HumanFacingPluginDefinition, ClassedPluginDefinition[Format]):
    """
    A (de)serialization format definition.
    """

    plugin_type_cls = Format
    type = PluginTypeDefinition(
        id="format",
        label=_("(De)serialization format"),
        discoveries=EntryPointDiscovery("betty.serde_format"),
    )


@final
class FormatStr(Localizable):
    """
    Localize and format a sequence of (de)serialization formats.
    """

    def __init__(self, serde_formats: Sequence[FormatDefinition]):
        self._serde_formats = serde_formats

    @override
    def localize(self, localizer: Localizer) -> Localized & str:
        return LocalizedStr(
            ", ".join(
                [
                    f"{extension} ({serde_format.label.localize(localizer)})"
                    for serde_format in self._serde_formats
                    for extension in serde_format.cls.media_type().extensions
                ]
            )
        )


def format_for(
    available_formats: Sequence[FormatDefinition], extension: str
) -> FormatDefinition:
    """
    Get the (de)serialization format for the given file extension.
    """
    for available_format in available_formats:
        if extension in available_format.cls.media_type().extensions:
            return available_format
    raise FormatError(
        _(
            'Unknown file format "{extension}". Supported formats are: {available_formats}.'
        ).format(extension=extension, available_formats=FormatStr(available_formats))
    )
