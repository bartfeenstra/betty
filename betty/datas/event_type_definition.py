"""
Event type definition data.
"""

from __future__ import annotations

from typing import final, override

from betty.datas.aggregate.record.object import ObjectDefinition
from betty.datas.countable_human_facing_plugin_definition import (
    CountableHumanFacingPluginDefinitionData,
)
from betty.datas.ordered_plugin_definition import OrderedPluginDefinitionData
from betty.event_type import EventType, EventTypeDefinition
from betty.locale import default_locale
from betty.locale.localizable.gettext import _
from betty.locale.localizable.static import CountableStaticTranslations
from betty.sample import Sample


@final
@ObjectDefinition(
    label=_("Event type configuration"),
    samples=[
        lambda: Sample(
            EventTypeDefinitionData(
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
    ],
)
class EventTypeDefinitionData(
    CountableHumanFacingPluginDefinitionData[EventTypeDefinition],
    OrderedPluginDefinitionData[EventTypeDefinition],
):
    """
    Configure a :py:class:`betty.event_type.EventTypeDefinition`.

    .. data:: betty.datas.event_type_definition:EventTypeDefinition
    """

    @override
    def new_plugin(self) -> EventTypeDefinition:
        @EventTypeDefinition(
            self.id,
            label=self.label,
            label_plural=self.label_plural,
            label_countable=self.label_countable,
            description=self.description,
            after=set(self.after),
            before=set(self.before),
        )
        class _EventTypeDefinitionDataEventType(EventType):
            pass

        return _EventTypeDefinitionDataEventType.plugin()
