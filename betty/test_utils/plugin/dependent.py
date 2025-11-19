"""
Test utilities for :py:mod:`betty.plugin.dependent`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from betty.machine_name import assert_machine_name
from betty.test_utils.plugin import PluginDefinitionTestBase

if TYPE_CHECKING:
    from betty.plugin.dependent import DependentPluginDefinition


class DependentPluginDefinitionTestBase(PluginDefinitionTestBase):
    """
    A base class for testing :py:class:`betty.plugin.dependent.DependentPluginDefinition` subclasses.
    """

    def test_depends_on(self, sut: DependentPluginDefinition) -> None:
        """
        Tests the :py:attr:`betty.plugin.dependent.DependentPluginDefinition.depends_on` value.
        """
        for plugin_id in sut.depends_on:
            assert_machine_name()(plugin_id)
