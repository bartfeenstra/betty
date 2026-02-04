"""
Test utilities for :py:mod:`betty.plugin.config`.
"""

from __future__ import annotations

from typing import final

from betty.plugin import Plugin, PluginDefinition, PluginTypeDefinition
from betty.test_utils.locale.localizable import DUMMY_COUNTABLE_LOCALIZABLE
from betty.test_utils.service.level import DummyConfigurable


class ConfigurableDummyPlugin(
    DummyConfigurable, Plugin["ConfigurableDummyPluginDefinition"]
):
    """
    A configurable dummy plugin.
    """


@final
@PluginTypeDefinition(
    "configurable-dummy-plugin",
    label="Configurable dummy plugin",
    label_plural="Configurable dummy plugins",
    label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
    discovery=[lambda _: [ConfigurableDummyPluginOne]],
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
