"""
Data for the Raspberry Mint extension.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from betty.collection.mapping import MutableResolvedMapping
from betty.collection.mapping.adapter import MutableResolvedMappingAdapter
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
from betty.plugins.extension.raspberry_mint.region import Region
from betty.property import Optional, Property
from betty.property.collection.mapping import MappingProperty
from betty.sample import Size

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from betty.plugin.factory import ResolvablePluginManufacturer
    from betty.plugins.extension.raspberry_mint.region import ResolvableRegion
    from betty.project import Project


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
    Configuration for the :py:class:`betty.plugins.extension.raspberry_mint.RaspberryMint` extension.

    .. data:: betty.plugins.extension.raspberry_mint.data:RaspberryMintConfiguration
    """

    primary_color = Optional(Property(ColorDefinition(), label=_("Primary color")))
    """
    The primary color.
    """

    secondary_color = Optional(Property(ColorDefinition(), label=_("Secondary color")))
    """
    The secondary color.
    """

    tertiary_color = Optional(Property(ColorDefinition(), label=_("Tertiary color")))
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
        from betty.plugins.extension.raspberry_mint.region import Region

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
