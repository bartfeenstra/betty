from __future__ import annotations

from typing import Any, TYPE_CHECKING

import pytest

from betty.assertion.error import AssertionFailed
from betty.model import UserFacingEntity
from betty.plugin.static import StaticPluginRepository
from betty.model.config import EntityReference
from betty.project.extension.cotton_candy.config import (
    ColorConfiguration,
    CottonCandyConfiguration,
)
from betty.test_utils.assertion.error import raises_error
from betty.test_utils.model import DummyEntity

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pytest_mock import MockerFixture
    from betty.serde.dump import Dump, DumpMapping


class TestColorConfiguration:
    async def test_hex_with_valid_value(self) -> None:
        hex_value = "#000000"
        sut = ColorConfiguration("#ffffff")
        sut.hex = hex_value
        assert sut.hex == hex_value

    @pytest.mark.parametrize(
        "hex_value",
        [
            "rgb(0,0,0)",
            "pink",
        ],
    )
    async def test_hex_with_invalid_value(self, hex_value: str) -> None:
        sut = ColorConfiguration("#ffffff")
        with pytest.raises(AssertionFailed):
            sut.hex = hex_value

    async def test_load_with_valid_hex_value(self) -> None:
        hex_value = "#000000"
        dump = hex_value
        sut = ColorConfiguration("#ffffff")
        sut.load(dump)
        assert sut.hex == hex_value

    @pytest.mark.parametrize(
        "dump",
        [
            False,
            123,
            "rgb(0,0,0)",
            "pink",
        ],
    )
    async def test_load_with_invalid_value(self, dump: Dump) -> None:
        sut = ColorConfiguration("#ffffff")
        with pytest.raises(AssertionFailed):
            sut.load(dump)

    async def test_dump_with_value(self) -> None:
        hex_value = "#000000"
        assert hex_value == ColorConfiguration(hex_value=hex_value).dump()


class CottonCandyConfigurationTestEntity(UserFacingEntity, DummyEntity):
    pass


class TestCottonCandyConfiguration:
    async def test_load_with_minimal_configuration(self) -> None:
        dump: Mapping[str, Any] = {}
        CottonCandyConfiguration().load(dump)

    async def test_load_without_dict_should_error(self) -> None:
        dump = None
        with raises_error(error_type=AssertionFailed):
            CottonCandyConfiguration().load(dump)

    async def test_load_with_featured_entities(self, mocker: MockerFixture) -> None:
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

    async def test_load_with_primary_inactive_color(self) -> None:
        hex_value = "#000000"
        dump: Dump = {
            "primary_inactive_color": hex_value,
        }
        sut = CottonCandyConfiguration()
        sut.load(dump)
        assert sut.primary_inactive_color.hex == hex_value

    async def test_load_with_primary_active_color(self) -> None:
        hex_value = "#000000"
        dump: Dump = {
            "primary_active_color": hex_value,
        }
        sut = CottonCandyConfiguration()
        sut.load(dump)
        assert sut.primary_active_color.hex == hex_value

    async def test_load_with_link_inactive_color(self) -> None:
        hex_value = "#000000"
        dump: Dump = {
            "link_inactive_color": hex_value,
        }
        sut = CottonCandyConfiguration()
        sut.load(dump)
        assert sut.link_inactive_color.hex == hex_value

    async def test_load_with_link_active_color(self) -> None:
        hex_value = "#000000"
        dump: Dump = {
            "link_active_color": hex_value,
        }
        sut = CottonCandyConfiguration()
        sut.load(dump)
        assert sut.link_active_color.hex == hex_value

    async def test_dump_with_minimal_configuration(self) -> None:
        sut = CottonCandyConfiguration()
        expected: DumpMapping[Dump] = {
            "featured_entities": [],
            "primary_inactive_color": CottonCandyConfiguration.DEFAULT_PRIMARY_INACTIVE_COLOR,
            "primary_active_color": CottonCandyConfiguration.DEFAULT_PRIMARY_ACTIVE_COLOR,
            "link_inactive_color": CottonCandyConfiguration.DEFAULT_LINK_INACTIVE_COLOR,
            "link_active_color": CottonCandyConfiguration.DEFAULT_LINK_ACTIVE_COLOR,
        }
        assert sut.dump() == expected

    async def test_dump_with_featured_entities(self) -> None:
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

    async def test_dump_with_primary_inactive_color(self) -> None:
        hex_value = "#000000"
        sut = CottonCandyConfiguration(primary_inactive_color=hex_value)
        dump = sut.dump()
        assert isinstance(dump, dict)
        assert hex_value == dump["primary_inactive_color"]

    async def test_dump_with_primary_active_color(self) -> None:
        hex_value = "#000000"
        sut = CottonCandyConfiguration(primary_active_color=hex_value)
        dump = sut.dump()
        assert isinstance(dump, dict)
        assert hex_value == dump["primary_active_color"]

    async def test_dump_with_link_inactive_color(self) -> None:
        hex_value = "#000000"
        sut = CottonCandyConfiguration(link_inactive_color=hex_value)
        dump = sut.dump()
        assert isinstance(dump, dict)
        assert hex_value == dump["link_inactive_color"]

    async def test_dump_with_link_active_color(self) -> None:
        hex_value = "#000000"
        sut = CottonCandyConfiguration(link_active_color=hex_value)
        dump = sut.dump()
        assert isinstance(dump, dict)
        assert hex_value == dump["link_active_color"]
