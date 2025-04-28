"""
Provide Betty's ancestry event types.
"""

from __future__ import annotations

from betty.mutability import Mutable
from betty.plugin import OrderedPlugin, PluginRepository
from betty.plugin.entry_point import EntryPointPluginRepository


class EventType(Mutable, OrderedPlugin["EventType"]):
    """
    Define an :py:class:`betty.ancestry.event.Event` type.

    Read more about :doc:`/development/plugin/event-type`.

    To test your own subclasses, use :py:class:`betty.test_utils.ancestry.event_type.EventTypeTestBase`.
    """


EVENT_TYPE_REPOSITORY: PluginRepository[EventType] = EntryPointPluginRepository(
    "betty.event_type"
)
"""
The event type plugin repository.

Read more about :doc:`/development/plugin/event-type`.
"""
