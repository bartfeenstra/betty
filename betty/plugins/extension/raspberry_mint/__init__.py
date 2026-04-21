"""
Provide the Raspberry Mint theme.
"""

from __future__ import annotations

from asyncio import gather
from collections import defaultdict
from enum import Enum
from typing import TYPE_CHECKING, Final, Self, final, override

from betty.content import Content, ContentManufacturer
from betty.extension import Extension, ExtensionDefinition
from betty.factory import DataManufacturable, Manufacturable
from betty.plugins.asset.raspberry_mint import RASPBERRY_MINT
from betty.plugins.extension.raspberry_mint.data import RaspberryMintConfiguration
from betty.plugins.extension.raspberry_mint.region import Region, ResolvableRegion
from betty.plugins.extension.webpack import Webpack
from betty.plugins.webpack_entry_point.raspberry_mint import (
    RaspberryMint as RaspberryMintWebpackEntryPoint,
)
from betty.project import Project
from betty.project.generate import Generator
from betty.service.simple import service

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence

    from betty.job.scheduler import Scheduler

type RegionalContent = Mapping[str, Sequence[Content]]
type RegionalContentManufacturers = Mapping[
    ResolvableRegion, Iterable[ContentManufacturer]
]


@final
@ExtensionDefinition(
    "raspberry-mint",
    label="Raspberry Mint",
    requires={
        Project.assets.require(RASPBERRY_MINT),
        Project.extensions.require(
            Webpack.entry_points, RaspberryMintWebpackEntryPoint
        ),
    },
)
class RaspberryMint(
    DataManufacturable[RaspberryMintConfiguration], Manufacturable, Generator, Extension
):
    """
    .. plugin:: extension:raspberry-mint.

    .. important::
        This extension requires :ref:`Node.js <installation-requirements-nodejs>`.

    Regions
    -------

    Raspberry Mint provides the following regions contents may be configured for:

    - ``front-page-content``
      The main content for the front page.
    - ``front-page-summary``
      The page summary for the front page.
    - ``entity-page-content``
      The page content region for entity pages.
    - ``entity-page-content--{entity_type_id}``
      The page content region for entity pages of a specific public-facing entity type, where ``{entity_type_id}`` is the
      entity type ID. If no content is assigned to this region for an entity type, ``entity-page-content`` is used instead.

    """

    DEFAULT_PRIMARY_COLOR: Final[str] = "#b3446c"
    DEFAULT_SECONDARY_COLOR: Final[str] = "#3eb489"
    DEFAULT_TERTIARY_COLOR: Final[str] = "#ffbd22"

    def __init__(
        self,
        *,
        project: Project,
        primary_color: str | None = None,
        regional_content: RegionalContentManufacturers | None = None,
        secondary_color: str | None = None,
        tertiary_color: str | None = None,
    ):
        super().__init__(services=project)
        self._project = project
        self._primary_color = (
            self.DEFAULT_PRIMARY_COLOR if primary_color is None else primary_color
        )
        self._regional_content_manufacturers = defaultdict(
            tuple,
            {}
            if regional_content is None
            else {
                Region.resolve(region): tuple(content)
                for region, content in regional_content.items()
            },
        )
        self._secondary_color = (
            self.DEFAULT_SECONDARY_COLOR if secondary_color is None else secondary_color
        )
        self._tertiary_color = (
            self.DEFAULT_TERTIARY_COLOR if tertiary_color is None else tertiary_color
        )

    @override
    @classmethod
    def new_data_cls(cls) -> type[RaspberryMintConfiguration]:
        return RaspberryMintConfiguration

    @override
    @Project.require
    @classmethod
    async def new(
        cls,
        project: Project,
        data: RaspberryMintConfiguration | None = None,
        /,
    ) -> Self:
        if data is None:
            return cls(project=project)
        return cls(
            primary_color=data.primary_color,
            project=project,
            regional_content=data.regional_content,
            secondary_color=data.secondary_color,
            tertiary_color=data.tertiary_color,
        )

    @override
    async def generate(self, scheduler: Scheduler) -> None:
        from betty.plugins.extension.raspberry_mint.jobs import (
            _GenerateLogo,
            _GenerateSearchIndex,
            _GenerateWebmanifest,
        )

        await scheduler.add(
            _GenerateLogo(project=self._project),
            _GenerateSearchIndex(project=self._project),
            _GenerateWebmanifest(project=self._project),
        )

    @service
    async def regional_content(self) -> RegionalContent:
        """
        The regional content.
        """
        return dict(
            zip(
                self._regional_content_manufacturers.keys(),
                await gather(*[
                    gather(
                        *map(
                            self._project.factory.new,
                            map(
                                ContentManufacturer.resolve,
                                region_content,
                            ),
                        )
                    )
                    for region_content in self._regional_content_manufacturers.values()
                ]),
                strict=False,
            )
        )

    @property
    def primary_color(self) -> str:
        """
        The primary color.
        """
        return self._primary_color

    @property
    def secondary_color(self) -> str:
        """
        The secondary color.
        """
        return self._secondary_color

    @property
    def tertiary_color(self) -> str:
        """
        The tertiary color.
        """
        return self._tertiary_color


@final
class ColorStyle(Enum):
    """
    The available color styles.
    """

    LIGHT = "light"
    """
    A light style with a white background.
    """

    LIGHT_SECONDARY = "light-secondary"
    """
    A light style with a light shade of the secondary color for the background.
    """

    LIGHT_CONTRAST = "light-contrast"
    """
    A light style with a light shade of gray for the background.
    """

    DARK = "dark"
    """
    A dark style with a black background.
    """

    DARK_SECONDARY = "dark-secondary"
    """
    A dark style with a dark shade of the secondary color for the background.
    """


@final
class Breakpoint(Enum):
    """
    The theme's breakpoints.
    """

    XS = "xs"
    SM = "sm"
    MD = "md"
    LG = "lg"
    XL = "xl"
    XXL = "xxl"


@final
class JustifyContent(Enum):
    """
    How to justify content.
    """

    START = "start"
    END = "end"
    CENTER = "center"
    BETWEEN = "between"
    AROUND = "around"
    EVENLY = "evenly"


SINGLE_COLUMN_TEXT_WIDTH = {
    Breakpoint.XS: 12,
    Breakpoint.LG: 11,
    Breakpoint.XL: 10,
    Breakpoint.XXL: 9,
}
