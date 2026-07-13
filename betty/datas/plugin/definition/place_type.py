"""
Place type definition data.
"""

from __future__ import annotations

from typing import final, override

from betty.datas.plugin.definition import PluginDefinitionDefinition
from betty.datas.plugin.definition.human_facing import (
    CountableHumanFacingPluginDefinitionData,
)
from betty.locale import default_locale
from betty.localizables.static import CountableStaticTranslations
from betty.place_type import PlaceType, PlaceTypeDefinition
from betty.sample import Sample


@final
@PluginDefinitionDefinition(
    PlaceTypeDefinition,
    samples=[
        lambda: Sample(
            PlaceTypeDefinitionData(
                id="moon",
                label="Moon",
                label_plural="Moons",
                label_countable=CountableStaticTranslations({
                    default_locale: {
                        "one": "{count} moon",
                        "other": "{count} moons",
                    }
                }),
            ),
            label="Default",
        )
    ],
)
class PlaceTypeDefinitionData(
    CountableHumanFacingPluginDefinitionData[PlaceTypeDefinition]
):
    """
    Configure a :py:class:`betty.place_type.PlaceTypeDefinition`.

    .. data:: betty.datas.plage_type_definition:PlaceTypeDefinitionData
    """

    @override
    def new_plugin(self) -> PlaceTypeDefinition:
        @PlaceTypeDefinition(
            self.id,
            label=self.label,
            label_plural=self.label_plural,
            label_countable=self.label_countable,
            description=self.description,
        )
        class _PlaceTypeDefinitionDataPlaceType(PlaceType):
            pass

        return _PlaceTypeDefinitionDataPlaceType.plugin()
