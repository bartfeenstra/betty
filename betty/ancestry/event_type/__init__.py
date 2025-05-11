"""
Provide Betty's ancestry event types.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from typing_extensions import override

from betty.locale.localizable import Localizable, _
from betty.mutability import Mutable
from betty.plugin import OrderedPlugin, Plugin, PluginRepository
from betty.plugin.entry_point import EntryPointPluginRepository

if TYPE_CHECKING:
    from betty.machine_name import MachineName


class EventType(Mutable, OrderedPlugin["EventType"]):
    """
    Define an :py:class:`betty.ancestry.event.Event` type.

    Read more about :doc:`/development/plugin/event-type`.

    To test your own subclasses, use :py:class:`betty.test_utils.ancestry.event_type.EventTypeTestBase`.
    """

    @final
    @override
    @classmethod
    def plugin_type_cls(cls) -> type[Plugin]:
        return EventType

    @final
    @override
    @classmethod
    def plugin_type_id(cls) -> MachineName:
        return "event-type"

    @final
    @override
    @classmethod
    def plugin_type_label(cls) -> Localizable:
        return _("Event type")


EVENT_TYPE_REPOSITORY: PluginRepository[EventType] = EntryPointPluginRepository(
    EventType, "betty.event_type"
)
"""
The event type plugin repository.

Read more about :doc:`/development/plugin/event-type`.
"""
