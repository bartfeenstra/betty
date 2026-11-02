from __future__ import annotations

from betty.datas.plugin.definition.role import RoleDefinitionData
from betty.test_utils.locale.localizable import (
    DUMMY_COUNTABLE_LOCALIZABLE,
)


class TestRoleDefinitionData:
    def test_new_plugin__minimal(self) -> None:
        plugin_id = "my-first-role"
        label = "My First Label"
        label_plural = "My First Labels"
        sut = RoleDefinitionData(
            id=plugin_id,
            label=label,
            label_plural=label_plural,
            label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
        )
        plugin = sut.new_plugin()
        assert plugin.id == plugin_id
        assert plugin.label == label
        assert plugin.label_plural == label_plural
        assert plugin.label_countable == DUMMY_COUNTABLE_LOCALIZABLE

    def test_new_plugin__full(self) -> None:
        description = "My First Description"
        sut = RoleDefinitionData(
            id="my-first-role",
            label="-",
            label_plural="-",
            label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
            description=description,
        )
        plugin = sut.new_plugin()
        assert plugin.description == description
