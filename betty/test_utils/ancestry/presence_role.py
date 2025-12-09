"""
Test utilities for :py:mod:`betty.ancestry.presence_role`.
"""

from __future__ import annotations

from betty.ancestry.presence_role import PresenceRole
from betty.test_utils.plugin import PluginTestBase
from betty.test_utils.plugin.human_facing import HumanFacingPluginDefinitionTestBase


class PresenceRoleDefinitionTestBase(HumanFacingPluginDefinitionTestBase):
    """
    A base class for testing :py:class:`betty.ancestry.presence_role.PresenceRoleDefinition` implementations.
    """


class PresenceRoleTestBase(PluginTestBase[PresenceRole]):
    """
    A base class for testing :py:class:`betty.ancestry.presence_role.PresenceRole` implementations.
    """
