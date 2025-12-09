"""
Configuration for themes.
"""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING, Self, final

from typing_extensions import override

from betty.assertion import assert_len, assert_mapping, assert_str
from betty.config import Configuration
from betty.content_provider import ContentProvider, ContentProviderDefinition
from betty.data import Key
from betty.exception import HumanFacingException, HumanFacingExceptionGroup
from betty.locale.localizable.gettext import _
from betty.locale.localizable.markup import Paragraph, do_you_mean
from betty.plugin.config import (
    PluginInstanceConfiguration,
    PluginInstanceConfigurationSequence,
)

if TYPE_CHECKING:
    from collections.abc import Collection, Mapping, MutableMapping, Sequence

    from betty.serde.dump import Dump


@final
class RegionalContentConfiguration(Configuration):
    """
    Configure content for regions.
    """

    def __init__(
        self,
        content: Mapping[
            str,
            PluginInstanceConfigurationSequence[
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
        ] = defaultdict(PluginInstanceConfigurationSequence)
        if content:
            self._content.update(content)

    def __getitem__(
        self, region: str
    ) -> PluginInstanceConfigurationSequence[
        ContentProviderDefinition, ContentProvider
    ]:
        return self._content[region]

    def __setitem__(
        self,
        region: str,
        content: Sequence[
            PluginInstanceConfiguration[ContentProviderDefinition, ContentProvider]
        ],
    ) -> None:
        self._content[region].clear()
        self._content[region].append(*content)

    @override
    @classmethod
    def load(cls, dump: Dump, /) -> Self:
        dump = assert_mapping(None, assert_str())(dump)
        assert_len(minimum=1)(dump)
        content: MutableMapping[
            str,
            PluginInstanceConfigurationSequence[
                ContentProviderDefinition, ContentProvider
            ],
        ] = {}
        with HumanFacingExceptionGroup() as errors:
            for region, region_dump in dump.items():
                with errors.absorb(Key(region)):
                    assert_len(minimum=1)(region_dump)
                    content[region] = PluginInstanceConfigurationSequence[
                        ContentProviderDefinition, ContentProvider
                    ].load(region_dump)
        return cls(content)

    @override
    def dump(self) -> Dump:
        return {
            region: region_configuration.dump()
            for region, region_configuration in self._content.items()
            if len(region_configuration)
        }

    def validate(self, available_regions: Collection[str], /) -> None:
        """
        Validate the configuration against runtime information.
        """
        with HumanFacingExceptionGroup() as errors:
            for region in self._content:
                with errors.absorb(Key(region)):
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
