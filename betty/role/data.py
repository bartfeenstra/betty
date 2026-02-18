"""
Role configuration.
"""

from __future__ import annotations

from typing import final, override

from betty.data.aggregate.record.object import ObjectDefinition
from betty.locale import DEFAULT_LOCALE
from betty.locale.localizable.gettext import _
from betty.locale.localizable.static import CountableStaticTranslations
from betty.plugin.config import CountableHumanFacingPluginDefinitionConfiguration
from betty.role import Role, RoleDefinition
from betty.sample import Sample


@final
@ObjectDefinition(
    label=_("Role configuration"),
    samples=[
        lambda: Sample(
            RoleDefinitionConfiguration(
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
class RoleDefinitionConfiguration(
    CountableHumanFacingPluginDefinitionConfiguration[RoleDefinition]
):
    """
    Configure a :py:class:`betty.role.RoleDefinition`.

    .. data:: betty.project.data:RoleDefinitionConfiguration
    """

    @override
    def new_plugin(self) -> RoleDefinition:
        @RoleDefinition(
            self.id,
            label=self.label,
            label_plural=self.label_plural,
            label_countable=self.label_countable,
            description=self.description,
        )
        class _ProjectConfigurationRole(Role):
            pass

        return _ProjectConfigurationRole.plugin()
