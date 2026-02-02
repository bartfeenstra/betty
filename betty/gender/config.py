"""
Gender configuration.
"""

from __future__ import annotations

from typing import final

from typing_extensions import override

from betty.data.aggregate.record.object import ObjectDefinition
from betty.gender import Gender, GenderDefinition
from betty.locale import DEFAULT_LOCALE
from betty.locale.localizable.gettext import _
from betty.locale.localizable.static import CountableStaticTranslations
from betty.plugin.config import CountableHumanFacingPluginDefinitionConfiguration
from betty.sample import Sample


@final
@ObjectDefinition(
    label=_("Gender configuration"),
    samples=[
        lambda: Sample(
            GenderDefinitionConfiguration(
                id="genderqueer",
                label="Genderqueer",
                label_plural="Genderqueers",
                label_countable=CountableStaticTranslations(
                    {
                        DEFAULT_LOCALE: {
                            "one": "{count} genderqueer",
                            "other": "{count} genderqueers",
                        }
                    }
                ),
            ),
            label="Default",
        )
    ],
)
class GenderDefinitionConfiguration(
    CountableHumanFacingPluginDefinitionConfiguration[GenderDefinition]
):
    """
    Configure a :py:class:`betty.gender.GenderDefinition`.

    .. data:: betty.project.config:GenderDefinitionConfiguration
    """

    @override
    def new_plugin(self) -> GenderDefinition:
        @GenderDefinition(
            self.id,
            label=self.label,
            label_plural=self.label_plural,
            label_countable=self.label_countable,
            description=self.description,
        )
        class _ProjectConfigurationGender(Gender):
            pass

        return _ProjectConfigurationGender.plugin()
