"""
Configuration for the Raspberry Mint extension.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self, final

from typing_extensions import override

from betty.assertion import OptionalField, assert_record
from betty.config import Configuration, Sample, get_full_sample, get_minimal_sample
from betty.config.color import ColorConfiguration
from betty.data import Key, Path
from betty.exception import reraise_within_context
from betty.project.extension.theme.config import RegionalContentConfiguration
from betty.project.factory import CallbackProjectDependentFactory

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.project import Project
    from betty.serde.dump import Dump, DumpMapping
    from betty.service.level.factory import AnyFactoryTarget


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

    DEFAULT_PRIMARY_COLOR = ColorConfiguration("#b3446c")
    DEFAULT_SECONDARY_COLOR = ColorConfiguration("#3eb489")
    DEFAULT_TERTIARY_COLOR = ColorConfiguration("#ffbd22")

    def __init__(
        self,
        *,
        primary_color: ColorConfiguration = DEFAULT_PRIMARY_COLOR,
        secondary_color: ColorConfiguration = DEFAULT_SECONDARY_COLOR,
        tertiary_color: ColorConfiguration = DEFAULT_TERTIARY_COLOR,
        regional_content: RegionalContentConfiguration | None = None,
    ):
        super().__init__()
        self._primary_color = primary_color
        self._secondary_color = secondary_color
        self._tertiary_color = tertiary_color
        self._regional_content = (
            RegionalContentConfiguration()
            if regional_content is None
            else regional_content
        )

    @override
    @property
    def validator(self) -> AnyFactoryTarget[None]:
        async def _validate(project: Project) -> None:
            from betty.project.extension.raspberry_mint import RaspberryMint

            extensions = await project.extensions
            with reraise_within_context(
                Key("regional_content"),
                Key("raspberry-mint"),
                Key("extensions"),
                Path(project.configuration_file_path),
            ):
                self.regional_content.validate(await extensions[RaspberryMint].regions)

        return CallbackProjectDependentFactory(_validate)

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
    @classmethod
    def load(cls, dump: Dump, /) -> Self:
        return cls(
            **assert_record(
                OptionalField("primary_color", ColorConfiguration.load),
                OptionalField("secondary_color", ColorConfiguration.load),
                OptionalField("tertiary_color", ColorConfiguration.load),
                OptionalField("regional_content", RegionalContentConfiguration.load),
            )(dump)
        )

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
    def samples(cls) -> Iterable[Sample[Self]]:
        yield Sample(cls(), label="Minimal", minimal=True)
        yield Sample(
            cls(
                primary_color=get_minimal_sample(ColorConfiguration).configuration,
                secondary_color=get_minimal_sample(ColorConfiguration).configuration,
                tertiary_color=get_minimal_sample(ColorConfiguration).configuration,
            ),
            label="Custom colors",
        )
        yield Sample(
            cls(
                regional_content=get_full_sample(
                    RegionalContentConfiguration
                ).configuration,
            ),
            label="Regional content",
        )
