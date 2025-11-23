"""
Test utilities for :py:mod:`betty.plugin.config`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Generic, TypeVar, cast, final

from betty.config import Configurable
from betty.locale.localizable import Plain
from betty.machine_name import MachineName
from betty.plugin import PluginDefinition, PluginTypeDefinition
from betty.plugin.classed import ClassedPluginDefinition
from betty.plugin.config import (
    PluginDefinitionConfiguration,
    PluginDefinitionConfigurationMapping,
)
from betty.plugin.discovery.callback import CallbackDiscovery
from betty.test_utils.config import DummyConfiguration
from betty.test_utils.config.collections.mapping import ConfigurationMappingTestBase

if TYPE_CHECKING:
    from betty.test_utils.config.collections import (
        ConfigurationCollectionTestBaseNewSut,
        ConfigurationCollectionTestBaseSutConfigurations,
    )

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


class ConfigurableDummyPlugin(Configurable[DummyConfiguration]):
    """
    A configurable dummy plugin.
    """

    plugin: ClassVar[ConfigurableDummyPluginDefinition]

    def __init__(self):
        super().__init__(configuration=DummyConfiguration())


class ConfigurableDummyPluginDefinition(
    ClassedPluginDefinition[ConfigurableDummyPlugin]
):
    """
    A definition of a configurable dummy plugin.
    """

    plugin_type_cls = ConfigurableDummyPlugin
    type = PluginTypeDefinition(
        id="configurable-dummy-plugin",
        label=Plain("Configurable dummy plugin"),
        discoveries=CallbackDiscovery(
            lambda: [
                ConfigurableDummyPluginOne.plugin,
            ]
        ),
    )


@final
@ConfigurableDummyPluginDefinition(
    id="configurable-dummy-plugin-one",
)
class ConfigurableDummyPluginOne(ConfigurableDummyPlugin):
    """
    A configurable dummy plugin (one).
    """
