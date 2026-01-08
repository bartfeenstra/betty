"""
Configuration for themes.
"""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING, Any, Self, final

from typing_extensions import override

from betty.assertion import assert_len, assert_mapping, assert_str
from betty.config import Configuration
from betty.content_provider import ContentProvider, ContentProviderDefinition
from betty.data import Sample
from betty.data.indicator.selector import Key
from betty.exception import HumanFacingException, reraise_with_indicator
from betty.locale.localizable.gettext import _
from betty.locale.localizable.markup import Paragraph, do_you_mean
from betty.plugin.config import (
    PluginInstanceConfiguration,
    PluginInstanceConfigurationSequence,
    ShorthandPluginInstanceConfigurationSequence,
)

if TYPE_CHECKING:
    from collections.abc import Collection, Iterable, Mapping, MutableMapping

    from betty.portable import PortableData


@final
class RegionalContentConfiguration(Configuration):
    """
    Configure content for regions.

    .. configuration:: betty.project.extension.theme.config:RegionalContentConfiguration
    """

    def __init__(
        self,
        content: Mapping[
            str,
            ShorthandPluginInstanceConfigurationSequence[
                ContentProviderDefinition, ContentProvider
            ],
        ]
        | None = None,
        /,
    ):
        super().__init__()
        self._content: MutableMapping[
            str,
            PluginInstanceConfigurationSequence[
                ContentProviderDefinition, ContentProvider
            ],
        ] = defaultdict(
            PluginInstanceConfigurationSequence[
                ContentProviderDefinition, ContentProvider
            ],
            {}
            if content is None
            else {
                region: PluginInstanceConfigurationSequence(region_content)  # ty:ignore[invalid-argument-type]
                for region, region_content in content.items()
            },
        )  # ty:ignore[no-matching-overload]

    def __getitem__(
        self, region: str
    ) -> PluginInstanceConfigurationSequence[
        ContentProviderDefinition, ContentProvider
    ]:
        return self._content[region]

    @override
    @classmethod
    def load(cls, portable: PortableData, /) -> Self:
        portable = assert_mapping(None, assert_str())(portable)
        assert_len(minimum=1)(portable)
        content: MutableMapping[
            str,
            PluginInstanceConfigurationSequence[
                ContentProviderDefinition, ContentProvider
            ],
        ] = {}
        for region, region_dump in portable.items():
            with reraise_with_indicator(Key(region)):
                assert_len(minimum=1)(region_dump)
                content[region] = PluginInstanceConfigurationSequence[
                    ContentProviderDefinition, ContentProvider
                ].load(region_dump)
        return cls(content)

    @override
    def dump(self) -> PortableData:
        return {
            region: region_configuration.dump()
            for region, region_configuration in self._content.items()
            if len(region_configuration)
        }

    @override
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented
        return self._content == other._content

    def validate(self, available_regions: Collection[str], /) -> None:
        """
        Validate the configuration against runtime information.
        """
        for region in self._content:
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

    @override
    @classmethod
    def samples(cls) -> Iterable[Sample[Self]]:  # ty:ignore[invalid-method-override]
        from betty.content_provider.content_providers import Render, RenderConfiguration

        yield Sample(
            cls(
                {
                    "a-theme-region": PluginInstanceConfiguration(
                        Render, RenderConfiguration("Hello, world!")
                    )
                }  # ty:ignore[invalid-argument-type]
            ),
            label="Default",
        )
