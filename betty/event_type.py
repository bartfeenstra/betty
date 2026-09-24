"""
Provide Betty's ancestry event types.
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Self, final

from betty.datas.aggregate.record.object import Object, ObjectDefinition
from betty.definition.cls import ClsDefinition
from betty.definition.human_facing import CountableHumanFacingDefinition
from betty.localizables.gettext import _, ngettext
from betty.plugin import PluginDefinition, PluginTypeDefinition
from betty.plugin.factory import (
    PluginManufacturer,
    PluginManufacturerDefinition,
    ResolvablePluginManufacturer,
)
from betty.plugin.ordered import (
    Order,
    OrderedPluginDefinition,
)

if TYPE_CHECKING:
    from betty.entities.person import Person
    from betty.localizable import CountableLocalizable, ResolvableLocalizable
    from betty.machine_name import ResolvableMachineName
    from betty.project import Project
    from betty.requirement import Requires


class EventType(Object["EventTypeDefinition"]):
    """
    Define an :py:class:`betty.entities.event.Event` type.
    """


class ShouldExistEventType(EventType, metaclass=ABCMeta):
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
    CountableHumanFacingDefinition,
    OrderedPluginDefinition,
    ClsDefinition[EventType],
    PluginDefinition,
    ObjectDefinition[EventType],
):
    """
    .. plugin_type:: event-type.
    """

    def __init__(
        self,
        event_type_id: ResolvableMachineName,
        *,
        label: ResolvableLocalizable,
        label_plural: ResolvableLocalizable,
        label_countable: CountableLocalizable,
        description: ResolvableLocalizable | None = None,
        after: Order[Self] = (),
        before: Order[Self] = (),
        requires: Requires = (),
    ):
        super().__init__(
            event_type_id,
            label=label,
            label_plural=label_plural,
            label_countable=label_countable,
            description=description,
            after=after,
            before=before,
            requires=requires,
        )


@final
@PluginManufacturerDefinition(EventTypeDefinition)
class EventTypeManufacturer(PluginManufacturer[EventTypeDefinition, EventType]):
    """
    The event type manufacturer.
    """


type ResolvableEventTypeManufacturer = ResolvablePluginManufacturer[
    EventTypeDefinition, EventTypeManufacturer
]
