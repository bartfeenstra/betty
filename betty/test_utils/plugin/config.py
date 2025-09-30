"""
Test utilities for :py:mod:`betty.plugin.config`.
"""

from collections.abc import Iterable
from typing import Generic, TypeVar

from typing_extensions import override

from betty.machine_name import MachineName
from betty.plugin import PluginDefinition
from betty.plugin.config import PluginConfiguration, PluginConfigurationMapping
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

    @override
    async def get_sut(
        self, configurations: Iterable[_PluginConfigurationT] | None = None
    ) -> PluginConfigurationMapping[_PluginDefinitionT, _PluginConfigurationT]:
        raise NotImplementedError

    async def test_new_plugins(self) -> None:
        """
        Tests :py:meth:`betty.plugin.config.PluginConfigurationMapping.new_plugins` implementations.
        """
        configurations = await self.get_configurations()
        sut = await self.get_sut(configurations)
        for configuration, plugin in zip(
            configurations, sut.new_plugins(), strict=True
        ):
            assert plugin.id == configuration.id
