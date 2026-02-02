from __future__ import annotations

from betty.locale.localizable.plain import Plain
from betty.place_type.config import PlaceTypeDefinitionConfiguration
from betty.test_utils.locale.localizable import (
    DUMMY_COUNTABLE_LOCALIZABLE,
    DUMMY_LOCALIZABLE,
)


class TestPlaceTypeDefinitionConfiguration:
    def test_new_plugin__minimal(self) -> None:
        plugin_id = "my-first-place-type"
        label = Plain("-")
        label_plural = Plain("-")
        sut = PlaceTypeDefinitionConfiguration(
            id=plugin_id,
            label=label,
            label_plural=label_plural,
            label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
        )
        plugin = sut.new_plugin()
        assert plugin.id == plugin_id
        assert plugin.label is label
        assert plugin.label_plural is label_plural
        assert plugin.label_countable is DUMMY_COUNTABLE_LOCALIZABLE

    def test_new_plugin__full(self) -> None:
        description = Plain("-")
        sut = PlaceTypeDefinitionConfiguration(
            id="my-first-place-type",
            label=DUMMY_LOCALIZABLE,
            label_plural=DUMMY_LOCALIZABLE,
            label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
            description=description,
        )
        plugin = sut.new_plugin()
        assert plugin.description is description
