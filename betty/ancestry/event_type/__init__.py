"""
Provide Betty's ancestry event types.
"""

from __future__ import annotations

from betty.plugin import Plugin, PluginRepository
from betty.plugin.entry_point import EntryPointPluginRepository


class EventType(Plugin):
    """
    Define an :py:class:`betty.ancestry.event.Event` type.

    Read more about :doc:`/development/plugin/event-type`.

    To test your own subclasses, use :py:class:`betty.test_utils.ancestry.event_type.EventTypeTestBase`.
    """

    @classmethod
    def comes_before(cls) -> set[type[EventType]]:
        """
        Get the event types that this event type comes before.

        The returned event types come after this event type.
        """
        return set()  # pragma: no cover

    @classmethod
    def comes_after(cls) -> set[type[EventType]]:
        """
        Get the event types that this event type comes after.

        The returned event types come before this event type.
        """
        return set()  # pragma: no cover


EVENT_TYPE_REPOSITORY: PluginRepository[EventType] = EntryPointPluginRepository(
    "betty.event_type"
)
"""
The event type plugin repository.

Read more about :doc:`/development/plugin/event-type`.
"""
