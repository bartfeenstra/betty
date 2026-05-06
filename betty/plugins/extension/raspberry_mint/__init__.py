"""
Provide the Raspberry Mint theme.
"""

from __future__ import annotations

from asyncio import gather
from collections import defaultdict
from enum import Enum
from typing import TYPE_CHECKING, Final, Self, final, override

from betty.collection.mapping import MutableResolvedMapping, ResolvedMapping
from betty.collection.mapping.adapter import (
    MutableResolvedMappingAdapter,
    ResolvedMappingAdapter,
)
from betty.content import Content, ContentDefinition, ContentManufacturer
from betty.data import Data
from betty.datas.aggregate.collection.mapping import MappingDefinition
from betty.datas.aggregate.record.object import ObjectDefinition
from betty.datas.color import ColorDefinition
from betty.datas.plugin_manufacturer_sequence import (
    PluginManufacturerSequenceDefinition,
)
from betty.datas.str import StrDefinition
from betty.dirs import WEBPACK_ENTRY_POINT_DIRECTORY
from betty.entity import EntityDefinition
from betty.exception import HumanFacingException, reraise_with_indicator
from betty.extension import ExtensionDefinition
from betty.factory import DataManufacturable, Manufacturable
from betty.indicator.selector import Attr, Key
from betty.locale.localizable.gettext import _
from betty.locale.localizable.markup import Paragraph, do_you_mean
from betty.plugin.factory import ResolvablePluginManufacturer
from betty.plugins.asset_directory.raspberry_mint import RASPBERRY_MINT
from betty.plugins.extension.webpack import Webpack
from betty.plugins.extension.webpack.build import EntryPointProvider
from betty.project import Project
from betty.project.generate import Generator
from betty.properties.collection.mapping import MappingProperty
from betty.property import AttrProperty, Optional
from betty.sample import Sample, Size
from betty.service import ServiceProvider
from betty.service.simple import service

if TYPE_CHECKING:
    from collections.abc import Collection, Iterable, Mapping, Sequence

    from _typeshed import StrPath

    from betty.job.scheduler import Scheduler

type RegionalContent = ResolvedMapping[str, ResolvableRegion, Sequence[Content]]
type RegionalContentManufacturers = Mapping[
    ResolvableRegion, Iterable[ResolvablePluginManufacturer[ContentDefinition, Content]]
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
class RaspberryMintData(Data):
    """
    Configuration for the :py:class:`betty.plugins.extension.raspberry_mint.RaspberryMint` extension.

    .. data:: betty.plugins.extension.raspberry_mint:RaspberryMintData
    """

    primary_color = Optional(AttrProperty(ColorDefinition(), label=_("Primary color")))
    """
    The primary color.
    """

    secondary_color = Optional(
        AttrProperty(ColorDefinition(), label=_("Secondary color"))
    )
    """
    The secondary color.
    """

    tertiary_color = Optional(
        AttrProperty(ColorDefinition(), label=_("Tertiary color"))
    )
    """
    The tertiary color.
    """

    regional_content = MappingProperty(
        MappingDefinition(
            cls=MutableResolvedMapping,
            factory=lambda: MutableResolvedMappingAdapter(
                {}, key_resolver=Region.resolve
            ),
            label=_("Regions"),
            key=StrDefinition(label=_("Region")),
            value=PluginManufacturerSequenceDefinition(
                ContentManufacturer, label=_("Regional content")
            ),
        ),
        default=dict,
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
            Iterable[ResolvablePluginManufacturer[ContentDefinition, Content]],
        ]
        | None = None,
    ):

        super().__init__()
        self.primary_color = primary_color
        self.secondary_color = secondary_color
        self.tertiary_color = tertiary_color
        if regional_content is not None:
            self.regional_content.update({
                Region.resolve(region): ContentManufacturer.resolve_sequence(content)
                for region, content in regional_content.items()
            })

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
@ExtensionDefinition(
    "raspberry-mint",
    label="Raspberry Mint",
    requires={
        Project.asset_directories.require(RASPBERRY_MINT),
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
        self._primary_color = (
            self.DEFAULT_PRIMARY_COLOR if primary_color is None else primary_color
        )
        self._regional_content_manufacturers: RegionalContentManufacturers = (
            regional_content or {}
        )
        self._secondary_color = (
            self.DEFAULT_SECONDARY_COLOR if secondary_color is None else secondary_color
        )
        self._tertiary_color = (
            self.DEFAULT_TERTIARY_COLOR if tertiary_color is None else tertiary_color
        )

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

    @override
    @classmethod
    def webpack_entry_point_directory(cls) -> StrPath:
        return WEBPACK_ENTRY_POINT_DIRECTORY / cls.plugin().id

    @override
    def webpack_entry_point_cache_keys(self) -> Sequence[str]:
        return (
            self._project.root_path,
            self._primary_color,
            self._secondary_color,
            self._tertiary_color,
        )

    @service
    async def regional_content(self) -> RegionalContent:
        """
        The regional content.
        """
        from betty.plugins.extension.raspberry_mint._default import (
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
                                map(ContentManufacturer.resolve, region_content),
                            )
                        )
                        for region_content in regional_content_manufacturers.values()
                    ]),
                    strict=False,
                ),
            ),
            key_resolver=Region.resolve,
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
