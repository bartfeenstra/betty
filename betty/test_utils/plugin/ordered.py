"""
Test utilities for :py:mod:`betty.plugin.ordered`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from betty.machine_name import assert_machine_name
from betty.test_utils.plugin import PluginDefinitionTestBase

if TYPE_CHECKING:
    from betty.plugin.ordered import OrderedPluginDefinition


class OrderedPluginDefinitionTestBase(PluginDefinitionTestBase):
    """
    A base class for testing :py:class:`betty.plugin.ordered.OrderedPluginDefinition` subclasses.
    """

    def test_comes_after(self, sut: OrderedPluginDefinition) -> None:
        """
        Tests the :py:attr:`betty.plugin.ordered.OrderedPluginDefinition.comes_after` value.
        """
        for plugin_id in sut.comes_after:
            assert_machine_name()(plugin_id)

    def test_comes_before(self, sut: OrderedPluginDefinition) -> None:
        """
        Tests the :py:attr:`betty.plugin.ordered.OrderedPluginDefinition.comes_before` value.
        """
        for plugin_id in sut.comes_before:
            assert_machine_name()(plugin_id)
