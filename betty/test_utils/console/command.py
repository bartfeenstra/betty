"""
Test utilities for :py:mod:`betty.console.command`.
"""

from betty.console.command import Command
from betty.test_utils.plugin import PluginTestBase
from betty.test_utils.plugin.human_facing import HumanFacingPluginDefinitionTestBase


class CommandDefinitionTestBase(HumanFacingPluginDefinitionTestBase):
    """
    A base class for testing :py:class:`betty.console.command.CommandDefinition` subclasses.
    """


class CommandTestBase(PluginTestBase[Command]):
    """
    A base class for testing :py:class:`betty.console.command.Command` implementations.
    """
