"""
Presence role configuration.
"""

from __future__ import annotations

from typing import final, override

from betty.data.aggregate.record.object import ObjectDefinition
from betty.locale import DEFAULT_LOCALE
from betty.locale.localizable.gettext import _
from betty.locale.localizable.static import CountableStaticTranslations
from betty.plugin.config import CountableHumanFacingPluginDefinitionConfiguration
from betty.presence_role import PresenceRole, PresenceRoleDefinition
from betty.sample import Sample


@final
@ObjectDefinition(
    label=_("Presence role configuration"),
    samples=[
        lambda: Sample(
            PresenceRoleDefinitionConfiguration(
                id="astronaut",
                label="Astronaut",
                label_plural="Astronauts",
                label_countable=CountableStaticTranslations(
                    {
                        DEFAULT_LOCALE: {
                            "one": "{count} astronaut",
                            "other": "{count} astronauts",
                        }
                    }
                ),
            ),
            label="Default",
        )
    ],
)
class PresenceRoleDefinitionConfiguration(
    CountableHumanFacingPluginDefinitionConfiguration[PresenceRoleDefinition]
):
    """
    Configure a :py:class:`betty.presence_role.PresenceRoleDefinition`.

    .. data:: betty.project.data:PresenceRoleDefinitionConfiguration
    """

    @override
    def new_plugin(self) -> PresenceRoleDefinition:
        @PresenceRoleDefinition(
            self.id,
            label=self.label,
            label_plural=self.label_plural,
            label_countable=self.label_countable,
            description=self.description,
        )
        class _ProjectConfigurationPresenceRole(PresenceRole):
            pass

        return _ProjectConfigurationPresenceRole.plugin()
