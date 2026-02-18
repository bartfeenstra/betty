"""
Event type configuration.
"""

from __future__ import annotations

from typing import final, override

from betty.data.aggregate.record.object import ObjectDefinition
from betty.event_type import EventType, EventTypeDefinition
from betty.locale import DEFAULT_LOCALE
from betty.locale.localizable.gettext import _
from betty.locale.localizable.static import CountableStaticTranslations
from betty.plugin.data import CountableHumanFacingPluginDefinitionConfiguration
from betty.plugin.data.ordered import OrderedPluginDefinitionConfiguration
from betty.sample import Sample


@final
@ObjectDefinition(
    label=_("Event type configuration"),
    samples=[
        lambda: Sample(
            EventTypeDefinitionConfiguration(
                id="moon-landing",
                label="Moon landing",
                label_plural="Moon landings",
                label_countable=CountableStaticTranslations(
                    {
                        DEFAULT_LOCALE: {
                            "one": "{count} moon landing",
                            "other": "{count} moon landings",
                        }
                    }
                ),
            ),
            label="Default",
        )
    ],
)
class EventTypeDefinitionConfiguration(
    CountableHumanFacingPluginDefinitionConfiguration[EventTypeDefinition],
    OrderedPluginDefinitionConfiguration[EventTypeDefinition],
):
    """
    Configure a :py:class:`betty.event_type.EventTypeDefinition`.

    .. data:: betty.project.data:EventTypeDefinitionConfiguration
    """

    @override
    def new_plugin(self) -> EventTypeDefinition:
        @EventTypeDefinition(
            self.id,
            label=self.label,
            label_plural=self.label_plural,
            label_countable=self.label_countable,
            description=self.description,
            comes_before=set(self.comes_before),
            comes_after=set(self.comes_after),
        )
        class _ProjectConfigurationEventType(EventType):
            pass

        return _ProjectConfigurationEventType.plugin()
