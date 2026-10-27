"""
Event type definition data.
"""

from __future__ import annotations

from typing import final, override

from betty.datas.definition.human_facing import (
    CountableHumanFacingDefinitionConfig,
)
from betty.datas.definition.ordered import OrderedDefinitionConfig
from betty.datas.plugin.definition import (
    PluginDefinitionConfig,
    PluginDefinitionConfigDefinition,
)
from betty.event_type import EventType, EventTypeDefinition
from betty.locale import default_locale
from betty.localizables.static import CountableStaticTranslations
from betty.sample import Sample, Samples


@final
@PluginDefinitionConfigDefinition(
    EventTypeDefinition,
    samples=Samples(
        lambda: Sample(
            EventTypeDefinitionConfig(
                id="moon-landing",
                label="Moon landing",
                label_plural="Moon landings",
                label_countable=CountableStaticTranslations({
                    default_locale: {
                        "one": "{count} moon landing",
                        "other": "{count} moon landings",
                    }
                }),
            ),
            label="Default",
        )
    ),
)
class EventTypeDefinitionConfig(
    CountableHumanFacingDefinitionConfig[EventTypeDefinition],
    OrderedDefinitionConfig[EventTypeDefinition],
    PluginDefinitionConfig[EventTypeDefinition],
):
    """
    Configure a :py:class:`betty.event_type.EventTypeDefinition`.
    """

    @override
    def new_definition(self) -> EventTypeDefinition:
        @EventTypeDefinition(
            self.id,
            label=self.label,
            label_plural=self.label_plural,
            label_countable=self.label_countable,
            description=self.description,
            after=set(self.after),
            before=set(self.before),
        )
        class _EventTypeDefinitionConfigEventType(EventType):
            pass

        return _EventTypeDefinitionConfigEventType.definition
