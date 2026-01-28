"""
Configuration for the Raspberry Mint extension.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import TYPE_CHECKING, TypeAlias, final

from typing_extensions import override

from betty.config.color import ColorConfiguration
from betty.content_provider import ContentProvider, ContentProviderDefinition
from betty.data import Data, DataDefinition, Sample
from betty.data.aggregate.collection.mapping import MappingDefinition
from betty.data.aggregate.record.object import ObjectDefinition
from betty.data.aggregate.record.object.property import Property
from betty.data.indicator.selector import Attr, Key
from betty.data.sample import Size
from betty.data.str import StrDefinition
from betty.exception import HumanFacingException, reraise_with_indicator
from betty.locale.localizable.gettext import _
from betty.locale.localizable.markup import Paragraph, do_you_mean
from betty.plugin.config import (
    ResolvablePluginConfiguration,
    resolve_plugin_configurations,
)
from betty.plugin.data import PluginConfigurationSequenceDefinition
from betty.requirement import Requirement
from betty.service.hydrate import Hydratable

if TYPE_CHECKING:
    from betty.service.level import ServiceLevel

ResolvableRegionalContent: TypeAlias = Mapping[
    str,
    Iterable[ResolvablePluginConfiguration[ContentProviderDefinition, ContentProvider]],
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
                primary_color=ColorConfiguration.samples().get(Size.MINIMAL).data,
                secondary_color=ColorConfiguration.samples().get(Size.MINIMAL).data,
                tertiary_color=ColorConfiguration.samples().get(Size.MINIMAL).data,
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
class RaspberryMintConfiguration(Data, Hydratable):
    """
    Configuration for the :py:class:`betty.project.extension.raspberry_mint.RaspberryMint` extension.

    .. data:: betty.project.extension.raspberry_mint.config:RaspberryMintConfiguration
    """

    primary_color = Property(
        DataDefinition(cls=ColorConfiguration, label=_("Primary color")),
        default=lambda: RaspberryMintConfiguration._default_primary_color(),
    )
    """
    The primary color.
    """

    secondary_color = Property(
        DataDefinition(cls=ColorConfiguration, label=_("Secondary color")),
        default=lambda: RaspberryMintConfiguration._default_secondary_color(),
    )
    """
    The secondary color.
    """

    tertiary_color = Property(
        DataDefinition(cls=ColorConfiguration, label=_("Tertiary color")),
        default=lambda: RaspberryMintConfiguration._default_tertiary_color(),
    )
    """
    The tertiary color.
    """

    regional_content = Property(
        MappingDefinition(
            cls=dict,
            label=_("Regions"),
            key=StrDefinition(label=_("Region")),
            item=PluginConfigurationSequenceDefinition(
                ContentProviderDefinition, label=_("Regional content")
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
        primary_color: ColorConfiguration | None = None,
        secondary_color: ColorConfiguration | None = None,
        tertiary_color: ColorConfiguration | None = None,
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
                    region: list(resolve_plugin_configurations(content))  # ty:ignore[invalid-argument-type]
                    for region, content in regional_content.items()
                }
            )

    @classmethod
    def _default_primary_color(cls) -> ColorConfiguration:
        return ColorConfiguration("#b3446c")

    @classmethod
    def _default_secondary_color(cls) -> ColorConfiguration:
        return ColorConfiguration("#3eb489")

    @classmethod
    def _default_tertiary_color(cls) -> ColorConfiguration:
        return ColorConfiguration("#ffbd22")

    @override
    async def hydrate(self, services: ServiceLevel, /) -> None:
        from betty.project.extension.raspberry_mint import RaspberryMint

        raspberry_mint = await RaspberryMint.requires(services, repr(self))
        if isinstance(raspberry_mint, Requirement):
            raise HumanFacingException(raspberry_mint)
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
