"""
Test utilities for :py:mod:`betty.event_type`.
"""

from __future__ import annotations

from betty.event_type import EventType
from betty.test_utils.definition.human_facing import HumanFacingDefinitionTestBase
from betty.test_utils.plugin import PluginTestBase
from betty.test_utils.plugin.ordered import OrderedPluginDefinitionTestBase


class EventTypeDefinitionTestBase(
    HumanFacingDefinitionTestBase, OrderedPluginDefinitionTestBase
):
    """
    A base class for testing :py:class:`betty.event_type.EventTypeDefinition` implementations.
    """


class EventTypeTestBase(PluginTestBase[EventType]):
    """
    A base class for testing :py:class:`betty.event_type.EventType` implementations.
    """
