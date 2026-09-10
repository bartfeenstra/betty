"""
Test utilities for :py:mod:`betty.plugin`.
"""

from __future__ import annotations

from typing import final

from betty.definition import HasDefinition
from betty.definition.cls import ClsDefinition
from betty.life_cycle import LifeCycle
from betty.plugin import PluginDefinition, PluginTypeDefinition
from betty.plugin.cls.factory import (
    ManufacturablePlugin,
    NewPlugin,
    NewPluginDefinition,
)
from betty.test_utils.locale.localizable import DUMMY_COUNTABLE_LOCALIZABLE


class DummyPlugin(HasDefinition["DummyPluginDefinition"]):
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
class DummyPluginDefinition(ClsDefinition[DummyPlugin], PluginDefinition):
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
@NewPluginDefinition(DummyPluginDefinition)
class NewDummyPlugin(NewPlugin[DummyPluginDefinition, DummyPlugin]):
    """
    The dummy plugin factory.
    """


type ManufacturableDummyPlugin = ManufacturablePlugin[
    DummyPluginDefinition, NewDummyPlugin, DummyPlugin
]
