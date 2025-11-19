"""
Test utilities for :py:mod:`betty.ancestry.event_type`.
"""

from __future__ import annotations

from betty.test_utils.plugin import (
    ClassedPluginDefinitionTestBase,
    HumanFacingPluginDefinitionTestBase,
)
from betty.test_utils.plugin.ordered import OrderedPluginDefinitionTestBase


class EventTypeDefinitionTestBase(
    HumanFacingPluginDefinitionTestBase,
    OrderedPluginDefinitionTestBase,
    ClassedPluginDefinitionTestBase,
):
    """
    A base class for testing :py:class:`betty.ancestry.event_type.EventTypeDefinition` implementations.
    """
