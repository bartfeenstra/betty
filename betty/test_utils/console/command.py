"""
Test utilities for :py:mod:`betty.console.command`.
"""

from betty.test_utils.plugin.human_facing import HumanFacingPluginDefinitionTestBase


class CommandPluginTestBase(HumanFacingPluginDefinitionTestBase):
    """
    A base class for testing :py:class:`betty.console.command.CommandPlugin` subclasses.
    """
