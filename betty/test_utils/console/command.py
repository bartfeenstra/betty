"""
Test utilities for :py:mod:`betty.console.command`.
"""

from betty.console.command import Command
from betty.test_utils.definition.human_facing import HumanFacingDefinitionTestBase
from betty.test_utils.plugin import PluginTestBase


class CommandDefinitionTestBase(HumanFacingDefinitionTestBase):
    """
    A base class for testing :py:class:`betty.console.command.CommandDefinition` subclasses.
    """


class CommandTestBase(PluginTestBase[Command]):
    """
    A base class for testing :py:class:`betty.console.command.Command` implementations.
    """
