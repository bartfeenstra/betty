"""
Test utilities for :py:mod:`betty.console.command`.
"""

from betty.test_utils.plugin.classed import ClassedPluginDefinitionTestBase
from betty.test_utils.plugin.human_facing import HumanFacingPluginDefinitionTestBase


class CommandDefinitionTestBase(
    HumanFacingPluginDefinitionTestBase, ClassedPluginDefinitionTestBase
):
    """
    A base class for testing :py:class:`betty.console.command.CommandDefinition` subclasses.
    """
