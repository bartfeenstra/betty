"""
Test utilities for :py:mod:`betty.console.command`.
"""

from betty.console.command import Command
from betty.test_utils.plugin import PluginTestBase


class CommandTestBase(PluginTestBase[Command]):
    """
    A base class for testing :py:class:`betty.console.command.Command` implementations.
    """
