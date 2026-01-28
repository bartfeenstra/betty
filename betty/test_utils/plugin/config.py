"""
Test utilities for :py:mod:`betty.plugin.config`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, TypeVar, final

from typing_extensions import override

from betty.config import Configuration
from betty.config.factory import ConfigurationDependentSelfFactory
from betty.plugin import Plugin, PluginDefinition, PluginTypeDefinition
from betty.plugin.config import PluginDefinitionConfiguration
from betty.plugin.discovery.callback import CallbackDiscovery
from betty.test_utils.config import DummyConfigurable
from betty.test_utils.data import DummyData
from betty.test_utils.locale.localizable import DUMMY_COUNTABLE_LOCALIZABLE

if TYPE_CHECKING:
    from betty.service.level.factory import ServiceLevelTarget

_ConfigurationT = TypeVar("_ConfigurationT", bound=Configuration)
_PluginT = TypeVar("_PluginT", bound=Plugin)
_PluginDefinitionT = TypeVar("_PluginDefinitionT", bound=PluginDefinition)
_PluginDefinitionConfigurationT = TypeVar(
    "_PluginDefinitionConfigurationT", bound=PluginDefinitionConfiguration
)


class ConfigurableDummyPlugin(
    DummyConfigurable,
    ConfigurationDependentSelfFactory[DummyData],
    Plugin["ConfigurableDummyPluginDefinition"],
):
    """
    A configurable dummy plugin.
    """

    def __init__(self, *, configuration: DummyData | None = None):
        super().__init__(
            configuration=DummyData() if configuration is None else configuration
        )

    @override
    @classmethod
    def new_for_configuration(
        cls, configuration: DummyData
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
