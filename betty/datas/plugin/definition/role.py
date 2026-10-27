"""
Role definition data.
"""

from __future__ import annotations

from typing import final, override

from betty.datas.definition.human_facing import (
    CountableHumanFacingDefinitionConfig,
)
from betty.datas.plugin.definition import (
    PluginDefinitionConfig,
    PluginDefinitionConfigDefinition,
)
from betty.locale import default_locale
from betty.localizables.static import CountableStaticTranslations
from betty.role import Role, RoleDefinition
from betty.sample import Sample, Samples


@final
@PluginDefinitionConfigDefinition(
    RoleDefinition,
    samples=Samples(
        lambda: Sample(
            RoleDefinitionConfig(
                id="astronaut",
                label="Astronaut",
                label_plural="Astronauts",
                label_countable=CountableStaticTranslations({
                    default_locale: {
                        "one": "{count} astronaut",
                        "other": "{count} astronauts",
                    }
                }),
            ),
            label="Default",
        )
    ),
)
class RoleDefinitionConfig(
    CountableHumanFacingDefinitionConfig[RoleDefinition],
    PluginDefinitionConfig[RoleDefinition],
):
    """
    Configure a :py:class:`betty.role.RoleDefinition`.

    .. data:: betty.datas.role_definitin:RoleDefinitionConfig
    """

    @override
    def new_definition(self) -> RoleDefinition:
        @RoleDefinition(
            self.id,
            label=self.label,
            label_plural=self.label_plural,
            label_countable=self.label_countable,
            description=self.description,
        )
        class _RoleDefinitionConfigRole(Role):
            pass

        return _RoleDefinitionConfigRole.definition
