"""
Provide serialization formats.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, final

from typing_extensions import override

from betty.exception import HumanFacingException
from betty.locale import HasLocale, HasLocaleStr
from betty.locale.localizable import Localizable
from betty.locale.localizable.gettext import _, ngettext
from betty.plugin import Plugin, PluginTypeDefinition
from betty.plugin.discovery.entry_point import EntryPointDiscovery
from betty.plugin.human_facing import HumanFacingPluginDefinition

if TYPE_CHECKING:
    from collections.abc import Sequence

    from betty.locale.localize import Localizer
    from betty.media_type import MediaType
    from betty.serde.dump import Dump
    from betty.typing import Void


class FormatError(HumanFacingException):
    """
    Raised when data that is being deserialized is provided in an unknown (undeserializable) format.
    """


class Format(ABC, Plugin["FormatDefinition"]):
    """
    Defines a serialization format.
    """

    @classmethod
    @abstractmethod
    def media_type(cls) -> MediaType:
        """
        The media type this format can serialize.
        """

    @abstractmethod
    def load(self, dump: str, /) -> Dump:
        """
        Deserialize data.

        :raise FormatError: Raised when the dump could not be loaded.
        """

    @abstractmethod
    def dump(self, dump: Dump | Void, /) -> str:
        """
        Serialize data.
        """


@final
@PluginTypeDefinition(
    "format",
    Format,
    _("Serialization format"),
    _("Serialization formats"),
    ngettext("{count} serialization format", "{count} serialization formats"),
    discovery=EntryPointDiscovery("betty.serde_format"),
)
class FormatDefinition(HumanFacingPluginDefinition[Format]):
    """
    A serialization format definition.
    """


@final
class FormatStr(Localizable):
    """
    Localize and format a sequence of serialization formats.
    """

    def __init__(self, serde_formats: Sequence[FormatDefinition], /):
        self._serde_formats = serde_formats

    @override
    def localize(self, localizer: Localizer, /) -> HasLocale & str:
        return HasLocaleStr(
            ", ".join(
                [
                    f"{extension} ({serde_format.label.localize(localizer)})"
                    for serde_format in self._serde_formats
                    for extension in serde_format.cls.media_type().extensions
                ]
            )
        )


def format_for(
    available_formats: Sequence[FormatDefinition], extension: str, /
) -> FormatDefinition:
    """
    Get the serialization format for the given file extension.
    """
    for available_format in available_formats:
        if extension in available_format.cls.media_type().extensions:
            return available_format
    raise FormatError(
        _(
            'Unknown file format "{extension}". Supported formats are: {available_formats}.'
        ).format(extension=extension, available_formats=FormatStr(available_formats))
    )
