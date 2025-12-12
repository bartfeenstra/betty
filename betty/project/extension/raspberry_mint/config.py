"""
Provide configuration for the Raspberry Mint extension.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final

from typing_extensions import override

from betty.assertion import OptionalField, assert_record
from betty.config import Configuration
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
    Provide configuration for the :py:class:`betty.project.extension.raspberry_mint.RaspberryMint` extension.
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
                self.regional_content.validate(extensions[RaspberryMint].regions)

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
