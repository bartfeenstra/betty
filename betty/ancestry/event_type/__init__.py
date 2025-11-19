"""
Provide Betty's ancestry event types.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, ClassVar, final

from betty.locale.localizable import _
from betty.plugin import (
    ClassedPlugin,
    ClassedPluginDefinition,
    HumanFacingPluginDefinition,
    PluginIdentifier,
    PluginTypeDefinition,
    resolve_id,
)
from betty.plugin.discovery.entry_point import EntryPointDiscovery
from betty.plugin.discovery.project import ProjectDiscovery
from betty.plugin.ordered import OrderedPluginDefinition

if TYPE_CHECKING:
    from betty.ancestry.person import Person
    from betty.machine_name import MachineName
    from betty.project import Project


class EventType(ClassedPlugin):
    """
    Define an :py:class:`betty.ancestry.event.Event` type.
    """

    plugin: ClassVar[EventTypeDefinition]


class ShouldExistEventType(EventType, ABC):
    """
    An event type that controls whether at least one event of this type should exist for a person.
    """

    @classmethod
    @abstractmethod
    async def should_exist(cls, project: Project, person: Person) -> bool:
        """
        Whether at least one event of this type should exist for the given person.
        """


@final
class EventTypeDefinition(
    HumanFacingPluginDefinition,
    OrderedPluginDefinition,
    ClassedPluginDefinition[EventType],
):
    """
    An event type definition.

    Read more about :doc:`/development/plugin/event-type`.
    """

    plugin_type_cls = EventType
    type = PluginTypeDefinition(
        id="event-type",
        label=_("Event type"),
        discoveries=[
            EntryPointDiscovery("betty.event_type"),
            ProjectDiscovery(
                lambda project: project.configuration.event_types.new_plugins(),
            ),
        ],
    )

    def __init__(
        self,
        *,
        indicates: PluginIdentifier[EventTypeDefinition, EventType] | None = None,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self._indicates = None if indicates is None else resolve_id(indicates)

    @property
    def indicates(self) -> MachineName | None:
        """
        Return whether events of this type (approximately) indicate that an event of the retuned type has happened.
        """
        return self._indicates
