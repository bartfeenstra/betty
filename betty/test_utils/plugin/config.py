"""
Test utilities for :py:mod:`betty.plugin.config`.
"""

from typing import Generic, TypeVar, cast

from betty.machine_name import MachineName
from betty.plugin import PluginDefinition
from betty.plugin.config import PluginConfiguration, PluginConfigurationMapping
from betty.test_utils.config.collections import (
    ConfigurationCollectionTestBaseNewSut,
    ConfigurationCollectionTestBaseSutConfigurations,
)
from betty.test_utils.config.collections.mapping import ConfigurationMappingTestBase

_PluginDefinitionT = TypeVar("_PluginDefinitionT", bound=PluginDefinition)
_PluginConfigurationT = TypeVar("_PluginConfigurationT", bound=PluginConfiguration)


class PluginConfigurationMappingTestBase(
    ConfigurationMappingTestBase[MachineName, _PluginConfigurationT],
    Generic[_PluginDefinitionT, _PluginConfigurationT],
):
    """
    A base class for testing :py:class:`betty.plugin.config.PluginConfigurationMapping` implementations.
    """

    def test_new_plugins(
        self,
        new_sut: ConfigurationCollectionTestBaseNewSut[
            _PluginConfigurationT, MachineName
        ],
        sut_configurations: ConfigurationCollectionTestBaseSutConfigurations[
            _PluginConfigurationT
        ],
    ) -> None:
        """
        Tests :py:meth:`betty.plugin.config.PluginConfigurationMapping.new_plugins` implementations.
        """
        sut = cast(
            PluginConfigurationMapping[_PluginDefinitionT, _PluginConfigurationT],
            new_sut(sut_configurations),
        )
        for configuration, plugin in zip(
            sut_configurations, sut.new_plugins(), strict=True
        ):
            assert plugin.id == configuration.id
