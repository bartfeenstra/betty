"""
Provide Betty's ancestry event types.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, final, override

from betty.definition.human_facing import CountableHumanFacingDefinition
from betty.locale.localizable.gettext import _, ngettext
from betty.plugin import Plugin, PluginTypeDefinition, ResolvableId, resolve_id
from betty.plugin.discovery.entry_point import EntryPointDiscovery
from betty.plugin.factory import PluginManufacturer
from betty.plugin.ordered import OrderedPluginDefinition
from betty.service.requirement.project import require_project

if TYPE_CHECKING:
    import builtins
    from collections.abc import Set

    from betty.ancestry.person import Person
    from betty.locale.localizable import CountableLocalizable, ResolvableLocalizable
    from betty.machine_name import MachineName, ResolvableMachineName
    from betty.project import Project


class EventType(Plugin["EventTypeDefinition"]):
    """
    Define an :py:class:`betty.ancestry.event.Event` type.
    """


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
@PluginTypeDefinition(
    "event-type",
    label=_("Event type"),
    label_plural=_("Event types"),
    label_countable=ngettext("{count} event type", "{count} event types"),
    discovery=[
        EntryPointDiscovery("betty.event_type"),
        require_project(
            lambda project: (
                configuration.new_plugin()
                for configuration in project.configuration.event_types
            )
        ),
    ],
)
class EventTypeDefinition(
    CountableHumanFacingDefinition, OrderedPluginDefinition[EventType]
):
    """
    .. plugin_type:: event-type.
    """

    def __init__(
        self,
        plugin_id: ResolvableMachineName,
        *,
        label: ResolvableLocalizable,
        label_plural: ResolvableLocalizable,
        label_countable: CountableLocalizable,
        description: ResolvableLocalizable | None = None,
        comes_before: Set[ResolvableId] | None = None,
        comes_after: Set[ResolvableId] | None = None,
        indicates: ResolvableId[EventTypeDefinition] | None = None,
    ):
        super().__init__(
            plugin_id,
            label=label,
            label_plural=label_plural,
            label_countable=label_countable,
            description=description,
            comes_before=comes_before,
            comes_after=comes_after,
        )
        self._indicates = None if indicates is None else resolve_id(indicates)

    @property
    def indicates(self) -> MachineName | None:
        """
        Return whether events of this type (approximately) indicate that an event of the retuned type has happened.
        """
        return self._indicates


@final
class EventTypeManufacturer(PluginManufacturer[EventTypeDefinition, EventType]):
    """
    The event type manufacturer.
    """

    @override
    @classmethod
    def type(cls) -> builtins.type[EventTypeDefinition]:
        return EventTypeDefinition
