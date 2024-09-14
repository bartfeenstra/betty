"""
Test utilities for :py:mod:`betty.plugin.config`.
"""

from typing import TypeVar, Generic

from betty.machine_name import MachineName
from betty.plugin.config import PluginConfiguration
from betty.test_utils.config.collections.mapping import ConfigurationMappingTestBase

_PluginConfigurationT = TypeVar("_PluginConfigurationT", bound=PluginConfiguration)


class PluginConfigurationMappingTestBase(
    ConfigurationMappingTestBase[MachineName, _PluginConfigurationT],
    Generic[_PluginConfigurationT],
):
    """
    A base class for testing :py:class:`betty.plugin.config.PluginConfigurationMapping` implementations.
    """

    def test_plugins(self) -> None:
        """
        Tests :py:meth:`betty.plugin.config.PluginConfigurationMapping.plugins` implementations.
        """
        raise AssertionError
