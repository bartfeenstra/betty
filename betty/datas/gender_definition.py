"""
Gender definition data.
"""

from __future__ import annotations

from typing import final, override

from betty.datas.aggregate.record.object import ObjectDefinition
from betty.datas.countable_human_facing_plugin_definition import (
    CountableHumanFacingPluginDefinitionData,
)
from betty.gender import Gender, GenderDefinition
from betty.locale import DEFAULT_LOCALE
from betty.locale.localizable.gettext import _
from betty.locale.localizable.static import CountableStaticTranslations
from betty.sample import Sample


@final
@ObjectDefinition(
    label=_("Gender configuration"),
    samples=[
        lambda: Sample(
            GenderDefinitionData(
                id="genderqueer",
                label="Genderqueer",
                label_plural="Genderqueers",
                label_countable=CountableStaticTranslations({
                    DEFAULT_LOCALE: {
                        "one": "{count} genderqueer",
                        "other": "{count} genderqueers",
                    }
                }),
            ),
            label="Default",
        )
    ],
)
class GenderDefinitionData(CountableHumanFacingPluginDefinitionData[GenderDefinition]):
    """
    Configure a :py:class:`betty.gender.GenderDefinition`.

    .. data:: betty.datas.gender_definition:GenderDefinitionData
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
        class _GenderDefinitionDataGender(Gender):
            pass

        return _GenderDefinitionDataGender.plugin()
