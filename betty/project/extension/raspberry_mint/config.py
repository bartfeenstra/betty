"""
Provide configuration for the Raspberry Mint extension.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from typing_extensions import override

from betty.assertion import OptionalField, assert_record
from betty.config import Configuration
from betty.project.extension._theme import ColorConfiguration
from betty.project.extension.theme.config import RegionalContentConfiguration

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence

    from betty.content_provider import ContentProvider, ContentProviderDefinition
    from betty.plugin.config import PluginInstanceConfiguration
    from betty.serde.dump import Dump, DumpMapping


class RaspberryMintConfiguration(Configuration):
    """
    Provide configuration for the :py:class:`betty.project.extension.raspberry_mint.RaspberryMint` extension.
    """

    DEFAULT_PRIMARY_COLOR = "#b3446c"
    DEFAULT_SECONDARY_COLOR = "#3eb489"
    DEFAULT_TERTIARY_COLOR = "#ffbd22"

    def __init__(
        self,
        *,
        primary_color: str = DEFAULT_PRIMARY_COLOR,
        secondary_color: str = DEFAULT_SECONDARY_COLOR,
        tertiary_color: str = DEFAULT_TERTIARY_COLOR,
        regional_content: Mapping[
            str,
            Sequence[
                PluginInstanceConfiguration[ContentProviderDefinition, ContentProvider]
            ],
        ]
        | None = None,
    ):
        super().__init__()
        self._primary_color = ColorConfiguration(primary_color)
        self._secondary_color = ColorConfiguration(secondary_color)
        self._tertiary_color = ColorConfiguration(tertiary_color)
        self._regional_content = RegionalContentConfiguration(regional_content or {})

    @override
    def get_mutables(self) -> Iterable[object]:
        return (
            self._primary_color,
            self._secondary_color,
            self._tertiary_color,
            self._regional_content,
        )

    @property
    def primary_color(self) -> ColorConfiguration:
        """
        The primary color.
        """
        return self._primary_color

    @property
    def secondary_color(self) -> ColorConfiguration:
        """
        The secondary color.
        """
        return self._secondary_color

    @property
    def tertiary_color(self) -> ColorConfiguration:
        """
        The tertiary color.
        """
        return self._tertiary_color

    @property
    def regional_content(self) -> RegionalContentConfiguration:
        """
        The regional content.
        """
        return self._regional_content

    @override
    def load(self, dump: Dump) -> None:
        self.assert_mutable()
        assert_record(
            OptionalField("primary_color", self.primary_color.load),
            OptionalField("secondary_color", self.secondary_color.load),
            OptionalField("tertiary_color", self.tertiary_color.load),
            OptionalField("regional_content", self.regional_content.load),
        )(dump)

    @override
    def dump(self) -> DumpMapping[Dump]:
        dump = {
            "primary_color": self.primary_color.dump(),
            "secondary_color": self.secondary_color.dump(),
            "tertiary_color": self.tertiary_color.dump(),
        }
        regional_content_dump = self.regional_content.dump()
        if regional_content_dump:
            dump["regional_content"] = regional_content_dump
        return dump
