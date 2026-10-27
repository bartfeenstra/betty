from __future__ import annotations

from betty.datas.plugin.definition.place_type import PlaceTypeDefinitionConfig
from betty.test_utils.locale.localizable import dummy_countable_localizable


class TestPlaceTypeDefinitionConfig:
    def test_new_definition__minimal(self) -> None:
        plugin_id = "my-first-place-type"
        label = "My First Label"
        label_plural = "My First Labels"
        sut = PlaceTypeDefinitionConfig(
            id=plugin_id,
            label=label,
            label_plural=label_plural,
            label_countable=dummy_countable_localizable,
        )
        plugin = sut.new_definition()
        assert plugin.id == plugin_id
        assert plugin.label == label
        assert plugin.label_plural == label_plural
        assert plugin.label_countable == dummy_countable_localizable

    def test_new_definition__full(self) -> None:
        description = "My First Description"
        sut = PlaceTypeDefinitionConfig(
            id="my-first-place-type",
            label="-",
            label_plural="-",
            label_countable=dummy_countable_localizable,
            description=description,
        )
        plugin = sut.new_definition()
        assert plugin.description == description
