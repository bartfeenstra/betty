"""
Test utilities for :py:mod:`betty.plugin`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.plugin import Plugin, PluginDefinition, PluginTypeDefinition
from betty.plugin.factory import PluginManufacturer
from betty.test_utils.locale.localizable import DUMMY_COUNTABLE_LOCALIZABLE

if TYPE_CHECKING:
    import builtins


class DummyPlugin(Plugin["DummyPluginDefinition"]):
    """
    A dummy plugin.
    """


@final
@PluginTypeDefinition(
    "dummy-plugin",
    label=" dummy plugin",
    label_plural=" dummy plugin",
    label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
)
class DummyPluginDefinition(PluginDefinition[DummyPlugin]):
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


@final
class DummyPluginManufacturer(PluginManufacturer[DummyPluginDefinition, DummyPlugin]):
    """
    The dummy plugin manufacturer.
    """

    @override
    @classmethod
    def type(cls) -> builtins.type[DummyPluginDefinition]:
        return DummyPluginDefinition
