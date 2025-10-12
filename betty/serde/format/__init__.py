"""
Provide serialization formats.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, ClassVar, final

from typing_extensions import override

from betty.exception import UserFacingException
from betty.locale.localizable import Localizable, _
from betty.locale.localized import Localized, LocalizedStr
from betty.plugin import (
    ClassedPluginDefinition,
    ClassedPluginTypeDefinition,
    UserFacingPluginDefinition,
)
from betty.plugin.static import StaticPluginRepository

if TYPE_CHECKING:
    from collections.abc import Sequence

    from betty.locale.localizer import Localizer
    from betty.serde.dump import Dump
    from betty.typing import Voidable


class FormatError(UserFacingException):
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
    def extensions(cls) -> Sequence[str]:
        """
        The file extensions this format can (de)serialize.

        Extensions must include a leading dot, and are returned in order of decreasing priority.
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
class FormatDefinition(UserFacingPluginDefinition, ClassedPluginDefinition[Format]):
    """
    A (de)serialization format definition.
    """

    type: ClassVar[ClassedPluginTypeDefinition] = ClassedPluginTypeDefinition(
        id="format",
        label=_("(De)serialization format)"),
        cls=Format,
    )


@final
class FormatRepository(StaticPluginRepository[FormatDefinition]):
    """
    Exposes the available (de)serialization formats.
    """

    def __init__(self):
        from betty.serde.format.formats import Json, Yaml

        super().__init__(FormatDefinition, Json.plugin, Yaml.plugin)

    def extensions(self) -> Sequence[str]:
        """
        All file extensions supported by the formats in this repository.

        Extensions include a leading dot, and are returned in order of decreasing priority.
        """
        return [
            extension
            for serde_format in self
            for extension in serde_format.cls.extensions()
        ]


FORMAT_REPOSITORY = FormatRepository()
"""
The (de)serialization format plugin repository.
"""


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
                    for extension in serde_format.cls.extensions()
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
        if extension in available_format.cls.extensions():
            return available_format
    raise FormatError(
        _(
            'Unknown file format "{extension}". Supported formats are: {available_formats}.'
        ).format(extension=extension, available_formats=FormatStr(available_formats))
    )
