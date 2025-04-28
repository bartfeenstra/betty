"""
Test utilities for :py:mod:`betty.ancestry.event_type`.
"""

from __future__ import annotations

from betty.ancestry.event_type import EventType
from betty.test_utils.plugin import (
    DummyPlugin,
    PluginTestBase,
    assert_plugin_identifier,
)


class EventTypeTestBase(PluginTestBase[EventType]):
    """
    A base class for testing :py:class:`betty.ancestry.event_type.EventType` implementations.
    """

    async def test_comes_after(self) -> None:
        """
        Tests :py:meth:`betty.ancestry.event_type.EventType.comes_after` implementations.
        """
        for event_type_id in self.get_sut_class().comes_after():
            assert_plugin_identifier(
                event_type_id,
                EventType,  # type: ignore[type-abstract]
            )

    async def test_comes_before(self) -> None:
        """
        Tests :py:meth:`betty.ancestry.event_type.EventType.comes_before` implementations.
        """
        for event_type_id in self.get_sut_class().comes_before():
            assert_plugin_identifier(
                event_type_id,
                EventType,  # type: ignore[type-abstract]
            )


class DummyEventType(DummyPlugin, EventType):
    """
    A dummy event type implementation.
    """
