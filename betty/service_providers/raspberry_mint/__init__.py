"""
Provide the Raspberry Mint theme.
"""

from __future__ import annotations

from asyncio import gather
from collections import defaultdict
from enum import Enum
from operator import not_
from typing import TYPE_CHECKING, Final, Self, final, override

from betty.asset_directories.raspberry_mint import raspberry_mint
from betty.attrs.owner import CollectionOwnerAttr, OwnerAttr
from betty.collection.mapping import ResolvedMapping
from betty.collections import _empty_frozen_mapping
from betty.collections.mapping.adapter import (
    MutableResolvedMappingAdapter,
    ResolvedMappingAdapter,
)
from betty.content_builder import (
    ContentBuilder,
    NewContentBuilder,
    ResolvableContentBuilderManufacturer,
)
from betty.content_builders.render import Render, RenderConfig
from betty.data import Data
from betty.datas.aggregate.collection.mapping import MutableMappingDefinition
from betty.datas.aggregate.record import FieldDefinition
from betty.datas.aggregate.record.object import ObjectDefinition
from betty.datas.color import ColorDefinition
from betty.datas.plugin.manufacturer.sequence import (
    NewPluginSequenceDefinition,
)
from betty.datas.str import StrDefinition
from betty.dirs import webpack_entry_point_directory
from betty.entity import EntityDefinition
from betty.exception import HumanFacingException, reraise_with_indicator
from betty.indicator.operator import Attr, Key
from betty.jobs._generate_raspberry_mint_search_index import (
    _GenerateRaspberryMintSearchIndex,
)
from betty.jobs.generate_logo import GenerateLogo
from betty.localizables.gettext import _
from betty.localizables.markup import Paragraph, do_you_mean
from betty.plugin.cls import ConfigurableIntegratable, new
from betty.porters.omit_field import OmitFieldPorter
from betty.project import Project
from betty.project.generate import Generator
from betty.prop import HasProps
from betty.sample import Sample, Size
from betty.service_provider import ServiceProviderDefinition
from betty.service_providers.webpack import Webpack
from betty.service_providers.webpack.build import EntryPointProvider
from betty.services.simple import service

if TYPE_CHECKING:
    from collections.abc import Collection, Iterable, Mapping, Sequence

    from betty.content_builders.raspberry_mint_columns import ResolvableColumnsWidth
    from betty.job.scheduler import Scheduler
    from betty.pathlib import StrPath

type RegionalContent = ResolvedMapping[str, ResolvableRegion, Sequence[ContentBuilder]]
type ResolvableRegionalContent = Mapping[
    ResolvableRegion, Iterable[ResolvableContentBuilderManufacturer]
]
type ManufacturableRegionalContent = Mapping[
    ResolvableRegion, Iterable[ResolvableContentBuilderManufacturer]
]


@final
@ObjectDefinition(
    label=_("Raspberry Mint configuration"),
    samples=[
        lambda: Sample(RaspberryMintConfig(), label="Minimal", size=Size.MINIMAL),
        lambda: Sample(
            RaspberryMintConfig(
                primary_color=ColorDefinition().samples.get(Size.MINIMAL).subject,
                secondary_color=ColorDefinition().samples.get(Size.MINIMAL).subject,
                tertiary_color=ColorDefinition().samples.get(Size.MINIMAL).subject,
            ),
            label="Custom colors",
        ),
        lambda: Sample(
            RaspberryMintConfig(
                regional_content={
                    "front-page-content": [
                        NewContentBuilder(Render, RenderConfig("Hello, world!")),
                    ]
                }
            ),
            label="Regional content",
        ),
    ],
)
class RaspberryMintConfig(Data, HasProps):
    """
    Configuration for the :py:class:`betty.service_providers.raspberry_mint.RaspberryMint` extension.

    .. data:: betty.service_providers.raspberry_mint:RaspberryMintData
    """

    primary_color = OwnerAttr(ColorDefinition(label=_("Primary color"))).optional
    """
    The primary color.
    """

    secondary_color = OwnerAttr(ColorDefinition(label=_("Secondary color"))).optional
    """
    The secondary color.
    """

    tertiary_color = OwnerAttr(ColorDefinition(label=_("Tertiary color"))).optional
    """
    The tertiary color.
    """

    regional_content = CollectionOwnerAttr(
        FieldDefinition(
            MutableMappingDefinition(
                manufacturer=lambda values: MutableResolvedMappingAdapter(
                    {} if values is None else dict(values), key_resolver=Region.resolve
                ),
                label=_("Regions"),
                key=StrDefinition(label=_("Region")),
                value=NewPluginSequenceDefinition(
                    NewContentBuilder, label=_("Regional content")
                ),
            ),
            optional=True,
            porter=OmitFieldPorter.new(not_),
        )
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
        regional_content: ResolvableRegionalContent = _empty_frozen_mapping,
    ):

        super().__init__()
        self.primary_color = primary_color
        self.secondary_color = secondary_color
        self.tertiary_color = tertiary_color
        self.regional_content.update(regional_content)

    async def validate(self, project: Project, /) -> None:
        """
        Validate the configuration.
        """
        available_regions = await Region.all(project)
        with reraise_with_indicator(Attr("regional_content")):
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
@ServiceProviderDefinition(
    "raspberry-mint",
    label="Raspberry Mint",
    config_cls=RaspberryMintConfig,
    requires={
        Project.asset_directories.require(raspberry_mint),
        Project.service_providers.require(Webpack),
    },
)
class RaspberryMint(
    EntryPointProvider[Project],
    ConfigurableIntegratable[RaspberryMintConfig],
    Generator,
):
    """
    .. plugin:: service-provider:raspberry-mint.

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
        regional_content: ManufacturableRegionalContent | None = None,
        secondary_color: str | None = None,
        tertiary_color: str | None = None,
    ):
        super().__init__(services=project)
        self.primary_color: Final[str] = (
            self.DEFAULT_PRIMARY_COLOR if primary_color is None else primary_color
        )
        """
        The primary color.
        """
        self._regional_content_manufacturers: ManufacturableRegionalContent = (
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
    @Project.require
    @classmethod
    async def new(
        cls,
        project: Project,
        config: RaspberryMintConfig | None = None,
        /,
    ) -> Self:
        if config is None:
            return cls(project=project)
        return cls(
            primary_color=config.primary_color,
            project=project,
            regional_content=config.regional_content,
            secondary_color=config.secondary_color,
            tertiary_color=config.tertiary_color,
        )

    @override
    async def generate(self, scheduler: Scheduler) -> None:
        from betty.jobs._generate_raspberry_mint_webmanifest import (
            _GenerateRaspberryMintWebmanifest,
        )

        await scheduler.add(
            GenerateLogo(project=self.services),
            _GenerateRaspberryMintSearchIndex(project=self.services),
            _GenerateRaspberryMintWebmanifest(project=self.services),
        )

    @override
    @classmethod
    def webpack_entry_point_directory(cls) -> StrPath:
        return webpack_entry_point_directory / cls.plugin().id

    @override
    def webpack_entry_point_cache_keys(self) -> Sequence[str]:
        return (
            self.services.root_path,
            self.primary_color,
            self.secondary_color,
            self.tertiary_color,
        )

    @service
    async def regional_content(self) -> RegionalContent:
        """
        The regional content.
        """
        from betty.service_providers.raspberry_mint._default import (
            DefaultRegionalContent,
        )

        async with DefaultRegionalContent(self.services) as content:
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
                                lambda manufacturer: new(manufacturer, self.services),
                                map(NewContentBuilder.resolve, region_content),
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


single_column_text_width: Final[ResolvableColumnsWidth] = {
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
