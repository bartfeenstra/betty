"""
Test utilities for :py:mod:`betty.ancestry.event_type`.
"""

from __future__ import annotations

from betty.test_utils.plugin import (
    ClassedPluginDefinitionTestBase,
    OrderedPluginDefinitionTestBase,
    UserFacingPluginDefinitionTestBase,
)


class EventTypeDefinitionTestBase(
    UserFacingPluginDefinitionTestBase,
    OrderedPluginDefinitionTestBase,
    ClassedPluginDefinitionTestBase,
):
    """
    A base class for testing :py:class:`betty.ancestry.event_type.EventTypeDefinition` implementations.
    """
