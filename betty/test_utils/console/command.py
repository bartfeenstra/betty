"""
Test utilities for :py:mod:`betty.console.command`.
"""

from betty.test_utils.plugin import (
    ClassedPluginDefinitionTestBase,
    HumanFacingPluginDefinitionTestBase,
)


class CommandDefinitionTestBase(
    HumanFacingPluginDefinitionTestBase, ClassedPluginDefinitionTestBase
):
    """
    A base class for testing :py:class:`betty.console.command.CommandDefinition` subclasses.
    """
