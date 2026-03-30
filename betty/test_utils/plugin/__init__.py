"""
Test utilities for :py:mod:`betty.plugin`.
"""

from __future__ import annotations

from typing import final, override

from betty.life_cycle import LifeCycle
from betty.plugin import PluginTypeDefinition
from betty.plugin.cls import Plugin, PluginClsDefinition
from betty.plugin.factory import PluginManufacturer
from betty.test_utils.locale.localizable import DUMMY_COUNTABLE_LOCALIZABLE


class DummyPlugin(Plugin["DummyPluginDefinition"]):
    """
    A dummy plugin.
    """


@final
@PluginTypeDefinition(
    "dummy-plugin",
    label="dummy plugin",
    label_plural="dummy plugin",
    label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
)
class DummyPluginDefinition(PluginClsDefinition[DummyPlugin]):
    """
    A definition of a dummy plugin.
    """


@final
@DummyPluginDefinition("dummy-plugin-one")
class DummyPluginOne(DummyPlugin):
    """
    A dummy plugin (one).
    """


@final
@DummyPluginDefinition("dummy-plugin-two")
class DummyPluginTwo(DummyPlugin):
    """
    A dummy plugin (two).
    """


@final
@DummyPluginDefinition("dummy-plugin-three")
class DummyPluginThree(DummyPlugin):
    """
    A dummy plugin (three).
    """


@final
@DummyPluginDefinition("dummy-plugin-four")
class DummyPluginFour(DummyPlugin):
    """
    A dummy plugin (four).
    """


@DummyPluginDefinition("dummy-plugin-with-life-cycle")
class DummyPluginWithLifeCycle(DummyPlugin, LifeCycle):
    """
    A dummy plugin that is also a life cycle.
    """

    def __init__(self):
        super().__init__()


@final
class DummyPluginManufacturer(PluginManufacturer[DummyPluginDefinition, DummyPlugin]):
    """
    The dummy plugin manufacturer.
    """

    @override
    @classmethod
    def plugin_type(cls) -> type[DummyPluginDefinition]:
        return DummyPluginDefinition
