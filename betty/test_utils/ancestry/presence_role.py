"""
Test utilities for :py:mod:`betty.ancestry.presence_role`.
"""

from __future__ import annotations

from betty.test_utils.plugin.classed import ClassedPluginDefinitionTestBase
from betty.test_utils.plugin.human_facing import HumanFacingPluginDefinitionTestBase


class PresenceRolePluginTestBase(
    HumanFacingPluginDefinitionTestBase,
    ClassedPluginDefinitionTestBase,
):
    """
    A base class for testing :py:class:`betty.ancestry.presence_role.PresenceRolePlugin` implementations.
    """
