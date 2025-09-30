"""
Test utilities for :py:mod:`betty.console.command`.
"""

from betty.test_utils.plugin import (
    ClassedPluginDefinitionTestBase,
    UserFacingPluginDefinitionTestBase,
)


class CommandDefinitionTestBase(
    UserFacingPluginDefinitionTestBase, ClassedPluginDefinitionTestBase
):
    """
    A base class for testing :py:class:`betty.console.command.CommandDefinition` subclasses.
    """
