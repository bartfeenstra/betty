"""
Test utilities for :py:mod:`betty.ancestry.event_type`.
"""

from __future__ import annotations

from betty.ancestry.event_type import EventType
from betty.test_utils.plugin import PluginTestBase
from betty.test_utils.plugin.human_facing import HumanFacingPluginDefinitionTestBase
from betty.test_utils.plugin.ordered import OrderedPluginDefinitionTestBase


class EventTypeDefinitionTestBase(
    HumanFacingPluginDefinitionTestBase, OrderedPluginDefinitionTestBase
):
    """
    A base class for testing :py:class:`betty.ancestry.event_type.EventTypeDefinition` implementations.
    """


class EventTypeTestBase(PluginTestBase[EventType]):
    """
    A base class for testing :py:class:`betty.ancestry.event_type.EventType` implementations.
    """
