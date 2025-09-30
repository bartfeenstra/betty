"""
Test utilities for :py:mod:`betty.ancestry.presence_role`.
"""

from __future__ import annotations

from betty.test_utils.plugin import (
    ClassedPluginDefinitionTestBase,
    UserFacingPluginDefinitionTestBase,
)


class PresenceRoleDefinitionTestBase(
    UserFacingPluginDefinitionTestBase,
    ClassedPluginDefinitionTestBase,
):
    """
    A base class for testing :py:class:`betty.ancestry.presence_role.PresenceRoleDefinition` implementations.
    """
