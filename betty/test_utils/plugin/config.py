"""
Test utilities for :py:mod:`betty.plugin.config`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final

from typing_extensions import override

from betty.plugin import Plugin, PluginDefinition, PluginTypeDefinition
from betty.plugin.discovery.callback import CallbackDiscovery
from betty.test_utils.config import DummyConfigurable
from betty.test_utils.data import DummyData
from betty.test_utils.locale.localizable import DUMMY_COUNTABLE_LOCALIZABLE

if TYPE_CHECKING:
    from betty.service.level import ServiceLevel


class ConfigurableDummyPlugin(
    DummyConfigurable, Plugin["ConfigurableDummyPluginDefinition"]
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
    async def new_for_configuration(
        cls, *, services: ServiceLevel, configuration: DummyData | None = None
    ) -> Self:
        return cls(configuration=configuration)


@PluginTypeDefinition(
    "configurable-dummy-plugin",
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
