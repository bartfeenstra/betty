"""
Place type configuration.
"""

from __future__ import annotations

from typing import final, override

from betty.data.aggregate.record.object import ObjectDefinition
from betty.locale import DEFAULT_LOCALE
from betty.locale.localizable.gettext import _
from betty.locale.localizable.static import CountableStaticTranslations
from betty.place_type import PlaceType, PlaceTypeDefinition
from betty.plugin.data import CountableHumanFacingPluginDefinitionConfiguration
from betty.sample import Sample


@final
@ObjectDefinition(
    label=_("Place type configuration"),
    samples=[
        lambda: Sample(
            PlaceTypeDefinitionConfiguration(
                id="moon",
                label="Moon",
                label_plural="Moons",
                label_countable=CountableStaticTranslations({
                    DEFAULT_LOCALE: {
                        "one": "{count} moon",
                        "other": "{count} moons",
                    }
                }),
            ),
            label="Default",
        )
    ],
)
class PlaceTypeDefinitionConfiguration(
    CountableHumanFacingPluginDefinitionConfiguration[PlaceTypeDefinition]
):
    """
    Configure a :py:class:`betty.place_type.PlaceTypeDefinition`.

    .. data:: betty.project.data:PlaceTypeDefinitionConfiguration
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
        class _ProjectConfigurationPlaceType(PlaceType):
            pass

        return _ProjectConfigurationPlaceType.plugin()
