from __future__ import annotations

from typing import Any, TYPE_CHECKING

from betty.assertion.error import AssertionFailed
from betty.model import UserFacingEntity
from betty.model.config import EntityReference
from betty.plugin.static import StaticPluginRepository
from betty.project.extension.cotton_candy.config import CottonCandyConfiguration
from betty.test_utils.assertion.error import raises_error
from betty.test_utils.model import DummyEntity

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pytest_mock import MockerFixture
    from betty.serde.dump import Dump, DumpMapping


class CottonCandyConfigurationTestEntity(UserFacingEntity, DummyEntity):
    pass


class TestCottonCandyConfiguration:
    async def test_load__with_minimal_configuration(self) -> None:
        dump: Mapping[str, Any] = {}
        CottonCandyConfiguration().load(dump)

    async def test_load__without_dict_should_error(self) -> None:
        dump = None
        with raises_error(error_type=AssertionFailed):
            CottonCandyConfiguration().load(dump)

    async def test_load__with_featured_entities(self, mocker: MockerFixture) -> None:
        mocker.patch(
            "betty.model.ENTITY_TYPE_REPOSITORY",
            new=StaticPluginRepository(CottonCandyConfigurationTestEntity),
        )
        entity_type = CottonCandyConfigurationTestEntity
        entity_id = "123"
        dump: Dump = {
            "featured_entities": [
                {
                    "entity_type": entity_type.plugin_id(),
                    "entity": entity_id,
                },
            ],
        }
        sut = CottonCandyConfiguration()
        sut.load(dump)
        assert sut.featured_entities[0].entity_type == entity_type.plugin_id()
        assert sut.featured_entities[0].entity_id == entity_id

    async def test_load__with_primary_inactive_color(self) -> None:
        hex_value = "#000000"
        dump: Dump = {
            "primary_inactive_color": hex_value,
        }
        sut = CottonCandyConfiguration()
        sut.load(dump)
        assert sut.primary_inactive_color.hex == hex_value

    async def test_load__with_primary_active_color(self) -> None:
        hex_value = "#000000"
        dump: Dump = {
            "primary_active_color": hex_value,
        }
        sut = CottonCandyConfiguration()
        sut.load(dump)
        assert sut.primary_active_color.hex == hex_value

    async def test_load__with_link_inactive_color(self) -> None:
        hex_value = "#000000"
        dump: Dump = {
            "link_inactive_color": hex_value,
        }
        sut = CottonCandyConfiguration()
        sut.load(dump)
        assert sut.link_inactive_color.hex == hex_value

    async def test_load__with_link_active_color(self) -> None:
        hex_value = "#000000"
        dump: Dump = {
            "link_active_color": hex_value,
        }
        sut = CottonCandyConfiguration()
        sut.load(dump)
        assert sut.link_active_color.hex == hex_value

    async def test_dump__with_minimal_configuration(self) -> None:
        sut = CottonCandyConfiguration()
        expected: DumpMapping[Dump] = {
            "featured_entities": [],
            "primary_inactive_color": CottonCandyConfiguration.DEFAULT_PRIMARY_INACTIVE_COLOR,
            "primary_active_color": CottonCandyConfiguration.DEFAULT_PRIMARY_ACTIVE_COLOR,
            "link_inactive_color": CottonCandyConfiguration.DEFAULT_LINK_INACTIVE_COLOR,
            "link_active_color": CottonCandyConfiguration.DEFAULT_LINK_ACTIVE_COLOR,
        }
        assert sut.dump() == expected

    async def test_dump__with_featured_entities(self) -> None:
        entity_type = CottonCandyConfigurationTestEntity
        entity_id = "123"
        sut = CottonCandyConfiguration(
            featured_entities=[EntityReference(entity_type, entity_id)],
        )
        expected = [
            {
                "entity_type": entity_type.plugin_id(),
                "entity": entity_id,
            },
        ]
        dump = sut.dump()
        assert isinstance(dump, dict)
        assert expected == dump["featured_entities"]

    async def test_dump__with_primary_inactive_color(self) -> None:
        hex_value = "#000000"
        sut = CottonCandyConfiguration(primary_inactive_color=hex_value)
        dump = sut.dump()
        assert isinstance(dump, dict)
        assert hex_value == dump["primary_inactive_color"]

    async def test_dump__with_primary_active_color(self) -> None:
        hex_value = "#000000"
        sut = CottonCandyConfiguration(primary_active_color=hex_value)
        dump = sut.dump()
        assert isinstance(dump, dict)
        assert hex_value == dump["primary_active_color"]

    async def test_dump__with_link_inactive_color(self) -> None:
        hex_value = "#000000"
        sut = CottonCandyConfiguration(link_inactive_color=hex_value)
        dump = sut.dump()
        assert isinstance(dump, dict)
        assert hex_value == dump["link_inactive_color"]

    async def test_dump__with_link_active_color(self) -> None:
        hex_value = "#000000"
        sut = CottonCandyConfiguration(link_active_color=hex_value)
        dump = sut.dump()
        assert isinstance(dump, dict)
        assert hex_value == dump["link_active_color"]

    def test_get_mutable_instances(self) -> None:
        sut = CottonCandyConfiguration()
        sut.immutable()
        assert sut.featured_entities.is_immutable
        assert sut.primary_active_color.is_immutable
        assert sut.primary_inactive_color.is_immutable
        assert sut.link_active_color.is_immutable
        assert sut.link_inactive_color.is_immutable
