"""
Test utilities for :py:mod:`betty.presence_role`.
"""

from __future__ import annotations

from betty.presence_role import PresenceRole
from betty.test_utils.definition.human_facing import HumanFacingDefinitionTestBase
from betty.test_utils.plugin import PluginTestBase


class PresenceRoleDefinitionTestBase(HumanFacingDefinitionTestBase):
    """
    A base class for testing :py:class:`betty.presence_role.PresenceRoleDefinition` implementations.
    """


class PresenceRoleTestBase(PluginTestBase[PresenceRole]):
    """
    A base class for testing :py:class:`betty.presence_role.PresenceRole` implementations.
    """
