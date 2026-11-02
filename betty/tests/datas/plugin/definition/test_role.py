from __future__ import annotations

from betty.datas.plugin.definition.role import RoleDefinitionData
from betty.test_utils.locale.localizable import dummy_countable_localizable


class TestRoleDefinitionData:
    def test_new_plugin__minimal(self) -> None:
        plugin_id = "my-first-role"
        label = "My First Label"
        label_plural = "My First Labels"
        sut = RoleDefinitionData(
            id=plugin_id,
            label=label,
            label_plural=label_plural,
            label_countable=dummy_countable_localizable,
        )
        plugin = sut.new_plugin()
        assert plugin.id == plugin_id
        assert plugin.label == label
        assert plugin.label_plural == label_plural
        assert plugin.label_countable == dummy_countable_localizable

    def test_new_plugin__full(self) -> None:
        description = "My First Description"
        sut = RoleDefinitionData(
            id="my-first-role",
            label="-",
            label_plural="-",
            label_countable=dummy_countable_localizable,
            description=description,
        )
        plugin = sut.new_plugin()
        assert plugin.description == description
