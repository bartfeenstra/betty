"""
Test utilities for :py:mod:`betty.plugin.config`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, Self, TypeVar, cast, final

from typing_extensions import override

from betty.config import Configuration
from betty.config.factory import ConfigurationDependentSelfFactory
from betty.machine_name import MachineName
from betty.plugin import Plugin, PluginDefinition, PluginTypeDefinition
from betty.plugin.config import (
    PluginDefinitionConfiguration,
    PluginDefinitionConfigurationMapping,
)
from betty.plugin.discovery.callback import CallbackDiscovery
from betty.plugin.resolve import ResolvableId
from betty.test_utils.config import DummyConfigurable, DummyConfiguration
from betty.test_utils.config.collections.mapping import ConfigurationMappingTestBase
from betty.test_utils.locale.localizable import DUMMY_COUNTABLE_LOCALIZABLE

if TYPE_CHECKING:
    from betty.service.level.factory import ServiceLevelTarget
    from betty.test_utils.config.collections import (
        ConfigurationCollectionTestBaseNewSut,
        ConfigurationCollectionTestBaseSutConfigurations,
    )

_ConfigurationT = TypeVar("_ConfigurationT", bound=Configuration)
_PluginT = TypeVar("_PluginT", bound=Plugin)
_PluginDefinitionT = TypeVar("_PluginDefinitionT", bound=PluginDefinition)
_PluginDefinitionConfigurationT = TypeVar(
    "_PluginDefinitionConfigurationT", bound=PluginDefinitionConfiguration
)


class PluginDefinitionConfigurationMappingTestBase(
    ConfigurationMappingTestBase[
        _ConfigurationT,
        MachineName,
        ResolvableId[_PluginDefinitionT],
        _PluginDefinitionConfigurationT,
    ],
    Generic[_ConfigurationT, _PluginDefinitionT, _PluginDefinitionConfigurationT],
):
    """
    A base class for testing :py:class:`betty.plugin.config.PluginDefinitionConfigurationMapping` implementations.
    """

    def test_new_plugins(
        self,
        new_sut: ConfigurationCollectionTestBaseNewSut[
            _PluginDefinitionConfigurationT,
            MachineName,
            ResolvableId[_PluginDefinitionT],
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


class ConfigurableDummyPlugin(
    DummyConfigurable,
    ConfigurationDependentSelfFactory[DummyConfiguration],
    Plugin["ConfigurableDummyPluginDefinition"],
):
    """
    A configurable dummy plugin.
    """

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
    ) -> ServiceLevelTarget[Self]:  # ty:ignore[invalid-method-override]
        return lambda: cls(configuration=configuration)


@PluginTypeDefinition(
    "configurable-dummy-plugin",
    base_cls=ConfigurableDummyPlugin,
    label="Configurable dummy plugin",
    label_plural="Configurable dummy plugins",
    label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
    discovery=CallbackDiscovery(
        lambda: [
            ConfigurableDummyPluginOne.plugin(),
        ]
    ),
)
class ConfigurableDummyPluginDefinition(PluginDefinition[ConfigurableDummyPlugin]):
    """
    A definition of a configurable dummy plugin.
    """


@final
@ConfigurableDummyPluginDefinition("configurable-dummy-plugin-one")
class ConfigurableDummyPluginOne(ConfigurableDummyPlugin):
    """
    A configurable dummy plugin (one).
    """
