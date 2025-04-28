"""
Provide serialization formats.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, final

from typing_extensions import override

from betty.assertion.error import AssertionFailed
from betty.locale.localizable import Localizable, _
from betty.locale.localized import LocalizedStr
from betty.plugin import Plugin, PluginRepository
from betty.plugin.entry_point import EntryPointPluginRepository

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Sequence

    from betty.locale.localizer import Localizer
    from betty.machine_name import MachineName
    from betty.serde.dump import Dump
    from betty.typing import Voidable


class FormatError(AssertionFailed):
    """
    Raised when data that is being deserialized is provided in an unknown (undeserializable) format.
    """


class Format(Plugin):
    """
    Defines a (de)serialization format.
    """

    @classmethod
    @abstractmethod
    def extensions(cls) -> set[str]:
        """
        The file extensions this format can (de)serialize.
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
class FormatRepository(PluginRepository[Format]):
    """
    Exposes the available (de)serialization formats.
    """

    def __init__(self):
        super().__init__()
        self._upstream = EntryPointPluginRepository[Format]("betty.serde_format")

    @override
    async def get(self, plugin_id: MachineName) -> type[Format]:
        return await self._upstream.get(plugin_id)

    @override
    def __aiter__(self) -> AsyncIterator[type[Format]]:
        return self._upstream.__aiter__()

    async def extensions(self) -> set[str]:
        """
        All file extensions supported by the formats in this repository.
        """
        return {
            extension
            async for serde_format in self
            for extension in serde_format.extensions()
        }


FORMAT_REPOSITORY = FormatRepository()
"""
The (de)serialization format plugin repository.

Read more about :doc:`/development/plugin/serde-format`.
"""


@final
class FormatStr(Localizable):
    """
    Localize and format a sequence of (de)serialization formats.
    """

    def __init__(self, serde_formats: Sequence[type[Format]]):
        self._serde_formats = serde_formats

    @override
    def localize(self, localizer: Localizer) -> LocalizedStr:
        return LocalizedStr(
            ", ".join(
                [
                    f"{extension} ({serde_format.plugin_label().localize(localizer)})"
                    for serde_format in self._serde_formats
                    for extension in serde_format.extensions()
                ]
            )
        )


def format_for(
    available_formats: Sequence[type[Format]], extension: str
) -> type[Format]:
    """
    Get the (de)serialization format for the given file extension.
    """
    for available_format in available_formats:
        if extension in available_format.extensions():
            return available_format
    raise FormatError(
        _(
            'Unknown file format "{extension}". Supported formats are: {available_formats}.'
        ).format(extension=extension, available_formats=FormatStr(available_formats))
    )
