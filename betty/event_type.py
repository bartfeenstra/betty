"""
Provide Betty's ancestry event types.
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, final

from betty.data import DataDefinitionCapabilityStage
from betty.definition.cls import ClsDefinitionCapabilityStage
from betty.definition.human_facing import CountableHumanFacingDefinition
from betty.localizables.gettext import _, ngettext
from betty.plugin import PluginTypeDefinition
from betty.plugin.data import DataPlugin, DataPluginDefinition
from betty.plugin.factory import PluginManufacturer, PluginManufacturerDefinition
from betty.plugin.ordered import (
    Order,
    OrderedPluginClsDefinition,
)
from betty.portable import Porter

if TYPE_CHECKING:
    from betty.entities.person import Person
    from betty.localizable import CountableLocalizable, ResolvableLocalizable
    from betty.machine_name import ResolvableMachineName
    from betty.project import Project
    from betty.requirement import Requires


class EventType(DataPlugin["EventTypeDefinition"]):
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
    CountableHumanFacingDefinition[
        DataDefinitionCapabilityStage | ClsDefinitionCapabilityStage
    ],
    OrderedPluginClsDefinition[
        EventType, DataDefinitionCapabilityStage | ClsDefinitionCapabilityStage
    ],
    DataPluginDefinition[EventType, Porter, DataDefinitionCapabilityStage],
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


@final
@PluginManufacturerDefinition(EventTypeDefinition)
class EventTypeManufacturer(PluginManufacturer[EventTypeDefinition, EventType]):
    """
    The event type manufacturer.
    """
