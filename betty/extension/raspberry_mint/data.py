"""
Data for the Raspberry Mint extension.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import TYPE_CHECKING, final

from betty.color import ColorDefinition
from betty.content import Content, ContentDefinition, ContentManufacturer
from betty.data import Data, Sample
from betty.data.aggregate.collection.mapping import MappingDefinition
from betty.data.aggregate.record.object import ObjectDefinition
from betty.data.indicator.selector import Attr, Key
from betty.data.str import StrDefinition
from betty.exception import HumanFacingException, reraise_with_indicator
from betty.locale.localizable.gettext import _
from betty.locale.localizable.markup import Paragraph, do_you_mean
from betty.plugin.data import PluginManufacturerSequenceDefinition
from betty.plugin.factory import ResolvablePluginManufacturer
from betty.property import Property
from betty.sample import Size

if TYPE_CHECKING:
    from betty.extension.raspberry_mint import RaspberryMint

type ResolvableRegionalContent = Mapping[
    str,
    Iterable[ResolvablePluginManufacturer[ContentDefinition, Content]],
]


@final
@ObjectDefinition(
    label=_("Raspberry Mint configuration"),
    samples=[
        lambda: Sample(
            RaspberryMintConfiguration(), label="Minimal", size=Size.MINIMAL
        ),
        lambda: Sample(
            RaspberryMintConfiguration(
                primary_color=ColorDefinition().samples.get(Size.MINIMAL).subject,
                secondary_color=ColorDefinition().samples.get(Size.MINIMAL).subject,
                tertiary_color=ColorDefinition().samples.get(Size.MINIMAL).subject,
            ),
            label="Custom colors",
        ),
        lambda: Sample(
            RaspberryMintConfiguration(
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
class RaspberryMintConfiguration(Data):
    """
    Configuration for the :py:class:`betty.extension.raspberry_mint.RaspberryMint` extension.

    .. data:: betty.extension.raspberry_mint.data:RaspberryMintConfiguration
    """

    DEFAULT_PRIMARY_COLOR = "#b3446c"
    DEFAULT_SECONDARY_COLOR = "#3eb489"
    DEFAULT_TERTIARY_COLOR = "#ffbd22"

    primary_color = Property(
        ColorDefinition(),
        label=_("Primary color"),
        default=lambda: RaspberryMintConfiguration.DEFAULT_PRIMARY_COLOR,
    )
    """
    The primary color.
    """

    secondary_color = Property(
        ColorDefinition(),
        label=_("Secondary color"),
        default=lambda: RaspberryMintConfiguration.DEFAULT_SECONDARY_COLOR,
    )
    """
    The secondary color.
    """

    tertiary_color = Property(
        ColorDefinition(),
        label=_("Tertiary color"),
        default=lambda: RaspberryMintConfiguration.DEFAULT_TERTIARY_COLOR,
    )
    """
    The tertiary color.
    """

    regional_content = Property(
        MappingDefinition(
            cls=dict,
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
        regional_content: ResolvableRegionalContent | None = None,
    ):
        super().__init__()
        if primary_color is not None:
            self.primary_color = primary_color
        if secondary_color is not None:
            self.secondary_color = secondary_color
        if tertiary_color is not None:
            self.tertiary_color = tertiary_color
        if regional_content is not None:
            self.regional_content.update(
                {
                    region: ContentManufacturer.resolve_sequence(content)
                    for region, content in regional_content.items()
                }
            )

    async def validate(self, raspberry_mint: RaspberryMint, /) -> None:
        """
        Validate the configuration.
        """
        available_regions = await raspberry_mint.regions
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
