"""
Provide the Raspberry Mint theme.
"""

from __future__ import annotations

from asyncio import gather
from collections import defaultdict
from enum import Enum
from typing import TYPE_CHECKING, Final, Self, final, override

from betty.asset_directories.raspberry_mint import raspberry_mint
from betty.attrs.owner import CollectionOwnerAttr, OwnerAttr
from betty.collection.mapping import MutableResolvedMapping, ResolvedMapping
from betty.collection.mapping.adapter import (
    MutableResolvedMappingAdapter,
    ResolvedMappingAdapter,
)
from betty.content import (
    ContentBuilder,
    ContentBuilderDefinition,
    ContentBuilderManufacturer,
)
from betty.data import Data
from betty.datas.aggregate.collection.mapping import MappingDefinition
from betty.datas.aggregate.record.object import ObjectDefinition
from betty.datas.color import ColorDefinition
from betty.datas.plugin_manufacturer_sequence import (
    PluginManufacturerSequenceDefinition,
)
from betty.datas.str import StrDefinition
from betty.dirs import webpack_entry_point_directory
from betty.entity import EntityDefinition
from betty.exception import HumanFacingException, reraise_with_indicator
from betty.extension import ExtensionDefinition
from betty.extensions.webpack import Webpack
from betty.extensions.webpack.build import EntryPointProvider
from betty.factory import DataManufacturable, Manufacturable
from betty.indicator.selector import Attr as AttrSelector
from betty.indicator.selector import Key
from betty.jobs._generate_raspberry_mint_search_index import (
    _GenerateRaspberryMintSearchIndex,
)
from betty.jobs.generate_logo import GenerateLogo
from betty.locale.localizable.gettext import _
from betty.locale.localizable.markup import Paragraph, do_you_mean
from betty.plugin.factory import ResolvablePluginManufacturer
from betty.project import Project
from betty.project.generate import Generator
from betty.prop import HasProps
from betty.sample import Sample, Size
from betty.service import ServiceProvider
from betty.services.simple import service

if TYPE_CHECKING:
    from collections.abc import Collection, Iterable, Mapping, Sequence

    from betty.content_builders.raspberry_mint_columns import ShorthandColumnsWidth
    from betty.job.scheduler import Scheduler
    from betty.pathlib import StrPath

type RegionalContent = ResolvedMapping[str, ResolvableRegion, Sequence[ContentBuilder]]
type RegionalContentManufacturers = Mapping[
    ResolvableRegion,
    Iterable[ResolvablePluginManufacturer[ContentBuilderDefinition, ContentBuilder]],
]


@final
@ObjectDefinition(
    label=_("Raspberry Mint configuration"),
    samples=[
        lambda: Sample(RaspberryMintData(), label="Minimal", size=Size.MINIMAL),
        lambda: Sample(
            RaspberryMintData(
                primary_color=ColorDefinition().samples.get(Size.MINIMAL).subject,
                secondary_color=ColorDefinition().samples.get(Size.MINIMAL).subject,
                tertiary_color=ColorDefinition().samples.get(Size.MINIMAL).subject,
            ),
            label="Custom colors",
        ),
        lambda: Sample(
            RaspberryMintData(
                regional_content={
                    "front-page-content": {
                        "id": "render",
                        "configuration": {
                            "content": "Hello, world!",
                        },
                    }
                }
            ),
            label="Regional content",
        ),
    ],
)
class RaspberryMintData(Data, HasProps):
    """
    Configuration for the :py:class:`betty.extensions.raspberry_mint.RaspberryMint` extension.

    .. data:: betty.extensions.raspberry_mint:RaspberryMintData
    """

    primary_color = OwnerAttr(ColorDefinition(), label=_("Primary color")).optional
    """
    The primary color.
    """

    secondary_color = OwnerAttr(ColorDefinition(), label=_("Secondary color")).optional
    """
    The secondary color.
    """

    tertiary_color = OwnerAttr(ColorDefinition(), label=_("Tertiary color")).optional
    """
    The tertiary color.
    """

    regional_content = CollectionOwnerAttr(
        MappingDefinition(
            cls=MutableResolvedMapping,
            factory=lambda: MutableResolvedMappingAdapter(
                {}, key_resolver=Region.resolve
            ),
            label=_("Regions"),
            key=StrDefinition(label=_("Region")),
            value=PluginManufacturerSequenceDefinition(
                ContentBuilderManufacturer, label=_("Regional content")
            ),
        ),
        omit_load=True,
        omit_dump=lambda data: not len(data),
    )
    """
    The regional content.
    """

    def __init__(
        self,
        *,
        primary_color: str | None = None,
        secondary_color: str | None = None,
        tertiary_color: str | None = None,
        regional_content: Mapping[
            ResolvableRegion,
            Iterable[
                ResolvablePluginManufacturer[ContentBuilderDefinition, ContentBuilder]
            ],
        ]
        | None = None,
    ):

        super().__init__()
        self.primary_color = primary_color
        self.secondary_color = secondary_color
        self.tertiary_color = tertiary_color
        if regional_content is not None:
            self.regional_content.update({
                Region.resolve(region): ContentBuilderManufacturer.resolve_sequence(
                    content
                )
                for region, content in regional_content.items()
            })

    async def validate(self, project: Project, /) -> None:
        """
        Validate the configuration.
        """
        available_regions = await Region.all(project)
        with reraise_with_indicator(AttrSelector("regional_content")):
            for region in self.regional_content:
                with reraise_with_indicator(Key(region)):
                    if region not in available_regions:
                        raise HumanFacingException(
                            Paragraph(
                                _("Invalid region {invalid_region}.").format(
                                    invalid_region=f'"{region}"',
                                ),
                                do_you_mean(
                                    *(
                                        f'"{available_region}"'
                                        for available_region in available_regions
                                    )
                                ),
                            )
                        ) from None


@final
@ExtensionDefinition(
    "raspberry-mint",
    label="Raspberry Mint",
    requires={
        Project.asset_directories.require(raspberry_mint),
        Project.extensions.require(Webpack),
    },
)
class RaspberryMint(
    DataManufacturable[RaspberryMintData],
    Manufacturable,
    Generator,
    EntryPointProvider,
    ServiceProvider,
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
        self.primary_color: Final[str] = (
            self.DEFAULT_PRIMARY_COLOR if primary_color is None else primary_color
        )
        """
        The primary color.
        """
        self._regional_content_manufacturers: RegionalContentManufacturers = (
            regional_content or {}
        )
        self.secondary_color = (
            self.DEFAULT_SECONDARY_COLOR if secondary_color is None else secondary_color
        )
        """
        The secondary color.
        """
        self.tertiary_color = (
            self.DEFAULT_TERTIARY_COLOR if tertiary_color is None else tertiary_color
        )
        """
        The tertiary color.
        """

    @override
    @classmethod
    def new_data_cls(cls) -> type[RaspberryMintData]:
        return RaspberryMintData

    @override
    @Project.require
    @classmethod
    async def new(
        cls,
        project: Project,
        data: RaspberryMintData | None = None,
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
        from betty.jobs._generate_raspberry_mint_webmanifest import (
            _GenerateRaspberryMintWebmanifest,
        )

        await scheduler.add(
            GenerateLogo(project=self._project),
            _GenerateRaspberryMintSearchIndex(project=self._project),
            _GenerateRaspberryMintWebmanifest(project=self._project),
        )

    @override
    @classmethod
    def webpack_entry_point_directory(cls) -> StrPath:
        return webpack_entry_point_directory / cls.plugin().id

    @override
    def webpack_entry_point_cache_keys(self) -> Sequence[str]:
        return (
            self._project.root_path,
            self.primary_color,
            self.secondary_color,
            self.tertiary_color,
        )

    @service
    async def regional_content(self) -> RegionalContent:
        """
        The regional content.
        """
        from betty.extensions.raspberry_mint._default import (
            DefaultRegionalContent,
        )

        async with DefaultRegionalContent(self._project) as content:
            regional_content_manufacturers = {
                **await content.get(),
                **self._regional_content_manufacturers,
            }
        return ResolvedMappingAdapter(
            defaultdict(
                tuple,
                zip(
                    map(Region.resolve, regional_content_manufacturers),
                    await gather(*[
                        gather(
                            *map(
                                self._project.factory.new,
                                map(ContentBuilderManufacturer.resolve, region_content),
                            )
                        )
                        for region_content in regional_content_manufacturers.values()
                    ]),
                    strict=False,
                ),
            ),
            key_resolver=Region.resolve,
        )


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


single_column_text_width: Final[ShorthandColumnsWidth] = {
    Breakpoint.XS: 12,
    Breakpoint.LG: 11,
    Breakpoint.XL: 10,
    Breakpoint.XXL: 9,
}


@final
class Region(Enum):
    """
    The available regions.
    """

    ENTITY_PAGE_CONTENT = "entity-page-content"
    FRONT_PAGE_CONTENT = "front-page-content"
    FRONT_PAGE_SUMMARY = "front-page-summary"

    @classmethod
    async def all(cls, project: Project, /) -> Collection[str]:
        """
        The available regions.
        """
        return {
            *(region.value for region in cls),
            *[
                f"entity-page-content--{entity_type.id}"
                async for entity_type in project.plugins[EntityDefinition]
                if entity_type.public_facing
            ],
        }

    @classmethod
    def resolve(cls, region: ResolvableRegion) -> str:
        """
        Resolve a region to its string name.
        """
        if isinstance(region, str):
            return region
        return region.value


type ResolvableRegion = Region | str
