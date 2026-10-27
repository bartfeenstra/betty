"""
Place type definition data.
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
from betty.place_type import PlaceType, PlaceTypeDefinition
from betty.sample import Sample, Samples


@final
@PluginDefinitionConfigDefinition(
    PlaceTypeDefinition,
    samples=Samples(
        lambda: Sample(
            PlaceTypeDefinitionConfig(
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
    ),
)
class PlaceTypeDefinitionConfig(
    CountableHumanFacingDefinitionConfig[PlaceTypeDefinition],
    PluginDefinitionConfig[PlaceTypeDefinition],
):
    """
    Configure a :py:class:`betty.place_type.PlaceTypeDefinition`.

    .. data:: betty.datas.plage_type_definition:PlaceTypeDefinitionConfig
    """

    @override
    def new_definition(self) -> PlaceTypeDefinition:
        @PlaceTypeDefinition(
            self.id,
            label=self.label,
            label_plural=self.label_plural,
            label_countable=self.label_countable,
            description=self.description,
        )
        class _PlaceTypeDefinitionConfigPlaceType(PlaceType):
            pass

        return _PlaceTypeDefinitionConfigPlaceType.definition
