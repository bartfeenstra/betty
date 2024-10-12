"""
Provide Betty's ancestry event types.
"""

from __future__ import annotations

from betty.plugin import PluginRepository, OrderedPlugin
from betty.plugin.entry_point import EntryPointPluginRepository


class EventType(OrderedPlugin["EventType"]):
    """
    Define an :py:class:`betty.ancestry.event.Event` type.

    Read more about :doc:`/development/plugin/event-type`.

    To test your own subclasses, use :py:class:`betty.test_utils.ancestry.event_type.EventTypeTestBase`.
    """

    pass


EVENT_TYPE_REPOSITORY: PluginRepository[EventType] = EntryPointPluginRepository(
    "betty.event_type"
)
"""
The event type plugin repository.

Read more about :doc:`/development/plugin/event-type`.
"""
