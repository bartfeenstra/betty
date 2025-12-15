"""
Provide Betty's ancestry event types.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, final

from betty.locale.localizable.gettext import _, ngettext
from betty.plugin import Plugin, PluginTypeDefinition
from betty.plugin.discovery.entry_point import EntryPointDiscovery
from betty.plugin.discovery.project import ProjectDiscovery
from betty.plugin.human_facing import CountableHumanFacingPluginDefinition
from betty.plugin.ordered import OrderedPluginDefinition
from betty.plugin.resolve import ResolvableId, resolve_id

if TYPE_CHECKING:
    from collections.abc import Set

    from betty.ancestry.person import Person
    from betty.locale.localizable import CountableLocalizable, LocalizableLike
    from betty.machine_name import MachineName
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
    EventType,
    _("Event type"),
    _("Event types"),
    ngettext("{count} event type", "{count} event types"),
    discovery=[
        EntryPointDiscovery("betty.event_type"),
        ProjectDiscovery(
            lambda project: project.configuration.event_types.new_plugins(),
        ),
    ],
)
class EventTypeDefinition(
    CountableHumanFacingPluginDefinition[EventType], OrderedPluginDefinition[EventType]
):
    """
    An event type definition.

    Read more about :doc:`/development/plugin/event-type`.
    """

    def __init__(
        self,
        plugin_id: MachineName,
        *,
        label: LocalizableLike,
        label_plural: LocalizableLike,
        label_countable: CountableLocalizable,
        description: LocalizableLike | None = None,
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
