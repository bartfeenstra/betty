"""
Configuration for the Raspberry Mint extension.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self, final

from typing_extensions import override

from betty.assertion import OptionalField, assert_record
from betty.config import Configuration
from betty.config.color import ColorConfiguration
from betty.data import Sample, Samples
from betty.data.indicator import Path
from betty.data.indicator.selector import Key
from betty.data.sample import Size
from betty.exception import reraise_with_indicator
from betty.project.extension.theme.config import RegionalContentConfiguration
from betty.project.factory import require_project
from betty.service.level.factory import CallbackServiceLevelDependentFactory

if TYPE_CHECKING:
    from betty.portable import PortableData, PortableMapping
    from betty.project import Project
    from betty.service.level.factory import ServiceLevelTarget


@final
class RaspberryMintConfiguration(Configuration):
    """
    Configuration for the :py:class:`betty.project.extension.raspberry_mint.RaspberryMint` extension.

    .. configuration:: betty.project.extension.raspberry_mint.config:RaspberryMintConfiguration

    ``primary_color``
    ^^^^^^^^^^^^^^^^^^^^^^^^^^
    :sup:`optional`

    The case-insensitive hexadecimal code for the primary color. Defaults to ``#b3446c``.

    ``secondary_color``
    ^^^^^^^^^^^^^^^^^^^^^^^^^^
    :sup:`optional`

    The case-insensitive hexadecimal code for the secondary color. Defaults to ``#3eb489``.

    ``tertiary_color``
    ^^^^^^^^^^^^^^^^^^^^^^^^^^
    :sup:`optional`

    The case-insensitive hexadecimal code for the tertiary color. Defaults to ``#ffbd22``.

    ``regional_content``
    ^^^^^^^^^^^^^^^^^^^^^
    :sup:`optional`

    Assign content to regions within this theme. Keys are theme regions, and values are sequences of
    :py:class:`content provider <betty.content_provider.ContentProviderDefinition>` instance configurations.

    ``regional_content[][].id``
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~
    :sup:`required`

    The plugin ID of the content provider to assign to this region.

    ``regional_content[][].configuration``
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    :sup:`optional`

    The configuration for the content provider, if needed.
    """

    def __init__(
        self,
        *,
        primary_color: ColorConfiguration | None = None,
        secondary_color: ColorConfiguration | None = None,
        tertiary_color: ColorConfiguration | None = None,
        regional_content: RegionalContentConfiguration | None = None,
    ):
        super().__init__()
        self._primary_color = (
            self._default_primary_color() if primary_color is None else primary_color
        )
        self._secondary_color = (
            self._default_secondary_color()
            if secondary_color is None
            else secondary_color
        )
        self._tertiary_color = (
            self._default_tertiary_color() if tertiary_color is None else tertiary_color
        )
        self._regional_content = (
            RegionalContentConfiguration()
            if regional_content is None
            else regional_content
        )

    def _default_primary_color(self) -> ColorConfiguration:
        return ColorConfiguration("#b3446c")

    def _default_secondary_color(self) -> ColorConfiguration:
        return ColorConfiguration("#3eb489")

    def _default_tertiary_color(self) -> ColorConfiguration:
        return ColorConfiguration("#ffbd22")

    @override
    @property
    def validator(self) -> ServiceLevelTarget[None]:
        @require_project
        async def _validate(project: Project) -> None:
            from betty.project.extension.raspberry_mint import RaspberryMint

            extensions = await project.extensions
            with reraise_with_indicator(
                Key("regional_content"),
                Key("raspberry-mint"),
                Key("extensions"),
                Path(project.configuration_file_path),
            ):
                self.regional_content.validate(await extensions[RaspberryMint].regions)

        return CallbackServiceLevelDependentFactory(_validate)

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
    @classmethod
    def load(cls, portable: PortableData, /) -> Self:
        return cls(
            **assert_record(
                OptionalField("primary_color", ColorConfiguration.load),
                OptionalField("secondary_color", ColorConfiguration.load),
                OptionalField("tertiary_color", ColorConfiguration.load),
                OptionalField("regional_content", RegionalContentConfiguration.load),
            )(portable)
        )

    @override
    def dump(self) -> PortableMapping:
        portable: PortableMapping = {}
        if self.primary_color != self._default_primary_color():
            portable["primary_color"] = self.primary_color.dump()
        if self.secondary_color != self._default_secondary_color():
            portable["secondary_color"] = self.secondary_color.dump()
        if self.tertiary_color != self._default_tertiary_color():
            portable["tertiary_color"] = self.tertiary_color.dump()
        portable_regional_content = self.regional_content.dump()
        if portable_regional_content:
            portable["regional_content"] = portable_regional_content
        return portable

    @override
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented
        return (
            self.primary_color,
            self.secondary_color,
            self.tertiary_color,
            self.regional_content,
        ) == (
            other.primary_color,
            other.secondary_color,
            other.tertiary_color,
            other.regional_content,
        )

    @override
    @classmethod
    def samples(cls) -> Samples:
        return Samples(
            [
                lambda: Sample(cls(), label="Minimal", size=Size.MINIMAL),
                lambda: Sample(
                    cls(
                        primary_color=ColorConfiguration.samples()
                        .get(Size.MINIMAL)
                        .data,
                        secondary_color=ColorConfiguration.samples()
                        .get(Size.MINIMAL)
                        .data,
                        tertiary_color=ColorConfiguration.samples()
                        .get(Size.MINIMAL)
                        .data,
                    ),
                    label="Custom colors",
                ),
                lambda: Sample(
                    cls(
                        regional_content=RegionalContentConfiguration.samples()
                        .get(Size.FULL)
                        .data
                    ),
                    label="Regional content",
                ),
            ]
        )
