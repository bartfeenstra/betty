"""
Test utilities for :py:module:`betty.model.event_type`.
"""

from __future__ import annotations

from betty.model.event_type import EventType
from betty.test_utils.plugin import DummyPlugin, PluginTestBase


class EventTypeTestBase(PluginTestBase[EventType]):
    """
    A base class for testing :py:class:`betty.model.event_type.EventType` implementations.
    """

    pass


class DummyEventType(DummyPlugin, EventType):
    """
    A dummy event type implementation.
    """

    pass
