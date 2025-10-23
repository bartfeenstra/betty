"""
Test utilities for :py:mod:`betty.plugin.config`.
"""

from typing import Generic, TypeVar, cast

from betty.machine_name import MachineName
from betty.plugin import PluginDefinition
from betty.plugin.config import (
    PluginDefinitionConfiguration,
    PluginDefinitionConfigurationMapping,
)
from betty.test_utils.config.collections import (
    ConfigurationCollectionTestBaseNewSut,
    ConfigurationCollectionTestBaseSutConfigurations,
)
from betty.test_utils.config.collections.mapping import ConfigurationMappingTestBase

_PluginDefinitionT = TypeVar("_PluginDefinitionT", bound=PluginDefinition)
_PluginDefinitionConfigurationT = TypeVar(
    "_PluginDefinitionConfigurationT", bound=PluginDefinitionConfiguration
)


class PluginDefinitionConfigurationMappingTestBase(
    ConfigurationMappingTestBase[MachineName, _PluginDefinitionConfigurationT],
    Generic[_PluginDefinitionT, _PluginDefinitionConfigurationT],
):
    """
    A base class for testing :py:class:`betty.plugin.config.PluginDefinitionConfigurationMapping` implementations.
    """

    def test_new_plugins(
        self,
        new_sut: ConfigurationCollectionTestBaseNewSut[
            _PluginDefinitionConfigurationT, MachineName
        ],
        sut_configurations: ConfigurationCollectionTestBaseSutConfigurations[
            _PluginDefinitionConfigurationT
        ],
    ) -> None:
        """
        Tests :py:meth:`betty.plugin.config.PluginDefinitionConfigurationMapping.new_plugins` implementations.
        """
        sut = cast(
            PluginDefinitionConfigurationMapping[
                _PluginDefinitionT, _PluginDefinitionConfigurationT
            ],
            new_sut(sut_configurations),
        )
        for configuration, plugin in zip(
            sut_configurations, sut.new_plugins(), strict=True
        ):
            assert plugin.id == configuration.id
