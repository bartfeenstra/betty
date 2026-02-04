"""
Test utilities for :py:mod:`betty.plugin`.
"""

from __future__ import annotations

from typing import final

from betty.plugin import Plugin, PluginDefinition, PluginTypeDefinition
from betty.test_utils.locale.localizable import DUMMY_COUNTABLE_LOCALIZABLE


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
    discovery=[
        lambda _: [
            DummyPluginOne,
            DummyPluginTwo,
            DummyPluginThree,
            DummyPluginFour,
        ]
    ],
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
