"""
Provide Betty's ancestry event types.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, final

from betty.definition.human_facing import CountableHumanFacingDefinition
from betty.locale.localizable.gettext import _, ngettext
from betty.plugin import PluginTypeDefinition
from betty.plugin.cls import Plugin
from betty.plugin.factory import PluginManufacturer, PluginManufacturerDefinition
from betty.plugin.ordered import (
    Order,
    OrderedPluginClsDefinition,
)
from betty.plugin.resolve import ResolvablePluginId, resolve_plugin_id

if TYPE_CHECKING:
    from betty.entities.person import Person
    from betty.locale.localizable import CountableLocalizable, ResolvableLocalizable
    from betty.machine_name import MachineName, ResolvableMachineName
    from betty.project import Project
    from betty.requirement import Requires


class EventType(Plugin["EventTypeDefinition"]):
    """
    Define an :py:class:`betty.entities.event.Event` type.
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
)
class EventTypeDefinition(
    CountableHumanFacingDefinition, OrderedPluginClsDefinition[EventType]
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
        after: Order[EventTypeDefinition] = (),
        before: Order[EventTypeDefinition] = (),
        indicates: ResolvablePluginId[EventTypeDefinition] | None = None,
        requires: Requires = (),
    ):
        super().__init__(
            plugin_id,
            label=label,
            label_plural=label_plural,
            label_countable=label_countable,
            description=description,
            after=after,
            before=before,
            requires=requires,
        )
        self._indicates = None if indicates is None else resolve_plugin_id(indicates)

    @property
    def indicates(self) -> MachineName | None:
        """
        Return whether events of this type (approximately) indicate that an event of the retuned type has happened.
        """
        return self._indicates


@final
@PluginManufacturerDefinition(EventTypeDefinition)
class EventTypeManufacturer(PluginManufacturer[EventTypeDefinition, EventType]):
    """
    The event type manufacturer.
    """
