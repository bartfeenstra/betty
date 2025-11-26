"""
Test utilities for :py:mod:`betty.plugin.config`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Generic, Self, TypeVar, cast, final

from typing_extensions import override

from betty.config.factory import ConfigurationDependentSelfFactory
from betty.machine_name import MachineName
from betty.plugin import Plugin, PluginDefinition, PluginTypeDefinition
from betty.plugin.config import (
    PluginDefinitionConfiguration,
    PluginDefinitionConfigurationMapping,
)
from betty.plugin.discovery.callback import CallbackDiscovery
from betty.plugin.resolve import ResolvableId
from betty.test_utils.config import DummyConfiguration
from betty.test_utils.config.collections.mapping import ConfigurationMappingTestBase

if TYPE_CHECKING:
    from betty.service.level.factory import AnyFactoryTarget
    from betty.test_utils.config.collections import (
        ConfigurationCollectionTestBaseNewSut,
        ConfigurationCollectionTestBaseSutConfigurations,
    )

_PluginT = TypeVar("_PluginT", bound=Plugin)
_PluginDefinitionT = TypeVar("_PluginDefinitionT", bound=PluginDefinition)
_PluginDefinitionConfigurationT = TypeVar(
    "_PluginDefinitionConfigurationT", bound=PluginDefinitionConfiguration
)


class PluginDefinitionConfigurationMappingTestBase(
    ConfigurationMappingTestBase[
        MachineName,
        ResolvableId[_PluginDefinitionT, _PluginT],
        _PluginDefinitionConfigurationT,
    ],
    Generic[_PluginDefinitionT, _PluginT, _PluginDefinitionConfigurationT],
):
    """
    A base class for testing :py:class:`betty.plugin.config.PluginDefinitionConfigurationMapping` implementations.
    """

    def test_new_plugins(
        self,
        new_sut: ConfigurationCollectionTestBaseNewSut[
            _PluginDefinitionConfigurationT,
            MachineName,
            ResolvableId[_PluginDefinitionT, _PluginT],
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
                _PluginDefinitionT, _PluginT, _PluginDefinitionConfigurationT
            ],
            new_sut(sut_configurations),
        )
        for configuration, plugin in zip(
            sut_configurations, sut.new_plugins(), strict=True
        ):
            assert plugin.id == configuration.id


class ConfigurableDummyPlugin(
    ConfigurationDependentSelfFactory[DummyConfiguration], Plugin
):
    """
    A configurable dummy plugin.
    """

    plugin: ClassVar[ConfigurableDummyPluginDefinition]

    def __init__(self, *, configuration: DummyConfiguration | None = None):
        super().__init__(
            configuration=DummyConfiguration()
            if configuration is None
            else configuration
        )

    @override
    @classmethod
    def new_for_configuration(
        cls, configuration: DummyConfiguration
    ) -> AnyFactoryTarget[Self]:
        return lambda: cls(configuration=configuration)


class ConfigurableDummyPluginDefinition(PluginDefinition):
    """
    A definition of a configurable dummy plugin.
    """

    plugin_type_cls = ConfigurableDummyPlugin
    type = PluginTypeDefinition(
        "configurable-dummy-plugin",
        "Configurable dummy plugin",
        discoveries=CallbackDiscovery(
            lambda: [
                ConfigurableDummyPluginOne.plugin,
            ]
        ),
    )


@final
@ConfigurableDummyPluginDefinition("configurable-dummy-plugin-one")
class ConfigurableDummyPluginOne(ConfigurableDummyPlugin):
    """
    A configurable dummy plugin (one).
    """
