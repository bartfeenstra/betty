"""
Test utilities for :py:mod:`betty.ancestry.presence_role`.
"""

from __future__ import annotations

from betty.test_utils.plugin import (
    ClassedPluginDefinitionTestBase,
    HumanFacingPluginDefinitionTestBase,
)


class PresenceRoleDefinitionTestBase(
    HumanFacingPluginDefinitionTestBase,
    ClassedPluginDefinitionTestBase,
):
    """
    A base class for testing :py:class:`betty.ancestry.presence_role.PresenceRoleDefinition` implementations.
    """
