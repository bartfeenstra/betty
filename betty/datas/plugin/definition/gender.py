"""
Gender definition data.
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
from betty.gender import Gender, GenderDefinition
from betty.locale import default_locale
from betty.localizables.static import CountableStaticTranslations
from betty.sample import Sample, Samples


@final
@PluginDefinitionConfigDefinition(
    GenderDefinition,
    samples=Samples(
        lambda: Sample(
            GenderDefinitionConfig(
                id="genderqueer",
                label="Genderqueer",
                label_plural="Genderqueers",
                label_countable=CountableStaticTranslations({
                    default_locale: {
                        "one": "{count} genderqueer",
                        "other": "{count} genderqueers",
                    }
                }),
            ),
            label="Default",
        )
    ),
)
class GenderDefinitionConfig(
    CountableHumanFacingDefinitionConfig[GenderDefinition],
    PluginDefinitionConfig[GenderDefinition],
):
    """
    Configure a :py:class:`betty.gender.GenderDefinition`.
    """

    @override
    def new_definition(self) -> GenderDefinition:
        @GenderDefinition(
            self.id,
            label=self.label,
            label_plural=self.label_plural,
            label_countable=self.label_countable,
            description=self.description,
        )
        class _GenderDefinitionConfigGender(Gender):
            pass

        return _GenderDefinitionConfigGender.definition
