"""
Role definition data.
"""

from __future__ import annotations

from typing import final, override

from betty.datas.aggregate.record.object import ObjectDefinition
from betty.datas.countable_human_facing_plugin_definition import (
    CountableHumanFacingPluginDefinitionData,
)
from betty.locale import DEFAULT_LOCALE
from betty.locale.localizable.gettext import _
from betty.locale.localizable.static import CountableStaticTranslations
from betty.role import Role, RoleDefinition
from betty.sample import Sample


@final
@ObjectDefinition(
    label=_("Role configuration"),
    samples=[
        lambda: Sample(
            RoleDefinitionData(
                id="astronaut",
                label="Astronaut",
                label_plural="Astronauts",
                label_countable=CountableStaticTranslations({
                    DEFAULT_LOCALE: {
                        "one": "{count} astronaut",
                        "other": "{count} astronauts",
                    }
                }),
            ),
            label="Default",
        )
    ],
)
class RoleDefinitionData(CountableHumanFacingPluginDefinitionData[RoleDefinition]):
    """
    Configure a :py:class:`betty.role.RoleDefinition`.

    .. data:: betty.datas.role_definitin:RoleDefinitionData
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
        class _RoleDefinitionDataRole(Role):
            pass

        return _RoleDefinitionDataRole.plugin()
