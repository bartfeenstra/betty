from __future__ import annotations

from typing import TYPE_CHECKING, Any

from betty.exception import UserFacingException
from betty.model.config import EntityReference
from betty.project.extension.raspberry_mint.config import RaspberryMintConfiguration
from betty.test_utils.exception import raises_error
from betty.test_utils.model import DummyEntityOne

if TYPE_CHECKING:
    from collections.abc import Mapping

    from betty.serde.dump import Dump, DumpMapping


class TestRaspberryMintConfiguration:
    def test_featured_entities__from___init__(self) -> None:
        entity_reference = EntityReference(DummyEntityOne.plugin)
        sut = RaspberryMintConfiguration(featured_entities=[entity_reference])
        assert entity_reference in sut.featured_entities

    def test_primary_color__from___init__(self) -> None:
        hex_value = "#000000"
        sut = RaspberryMintConfiguration(primary_color=hex_value)
        assert sut.primary_color.hex == hex_value

    def test_secondary_color__from___init__(self) -> None:
        hex_value = "#000000"
        sut = RaspberryMintConfiguration(secondary_color=hex_value)
        assert sut.secondary_color.hex == hex_value

    def test_tertiary_color__from___init__(self) -> None:
        hex_value = "#000000"
        sut = RaspberryMintConfiguration(tertiary_color=hex_value)
        assert sut.tertiary_color.hex == hex_value

    def test_load__with_minimal_configuration(self) -> None:
        dump: Mapping[str, Any] = {}
        RaspberryMintConfiguration().load(dump)

    def test_load__without_dict_should_error(self) -> None:
        dump = None
        with raises_error(error_type=UserFacingException):
            RaspberryMintConfiguration().load(dump)

    def test_load__with_featured_entities(self) -> None:
        entity_type = DummyEntityOne.plugin
        entity_id = "123"
        dump: Dump = {
            "featured_entities": [
                {
                    "entity_type": entity_type.id,
                    "entity": entity_id,
                },
            ],
        }
        sut = RaspberryMintConfiguration()
        sut.load(dump)
        assert sut.featured_entities[0].entity_type == entity_type.id
        assert sut.featured_entities[0].entity_id == entity_id

    def test_load__with_primary_color(self) -> None:
        hex_value = "#000000"
        dump: Dump = {
            "primary_color": hex_value,
        }
        sut = RaspberryMintConfiguration()
        sut.load(dump)
        assert sut.primary_color.hex == hex_value

    def test_load__with_secondary_color(self) -> None:
        hex_value = "#000000"
        dump: Dump = {
            "secondary_color": hex_value,
        }
        sut = RaspberryMintConfiguration()
        sut.load(dump)
        assert sut.secondary_color.hex == hex_value

    def test_load__with_tertiary_color(self) -> None:
        hex_value = "#000000"
        dump: Dump = {
            "tertiary_color": hex_value,
        }
        sut = RaspberryMintConfiguration()
        sut.load(dump)
        assert sut.tertiary_color.hex == hex_value

    def test_dump__with_minimal_configuration(self) -> None:
        sut = RaspberryMintConfiguration()
        expected: DumpMapping[Dump] = {
            "featured_entities": [],
            "primary_color": RaspberryMintConfiguration.DEFAULT_PRIMARY_COLOR,
            "secondary_color": RaspberryMintConfiguration.DEFAULT_SECONDARY_COLOR,
            "tertiary_color": RaspberryMintConfiguration.DEFAULT_TERTIARY_COLOR,
        }
        assert sut.dump() == expected

    def test_dump__with_featured_entities(self) -> None:
        entity_type = DummyEntityOne.plugin
        entity_id = "123"
        sut = RaspberryMintConfiguration(
            featured_entities=[EntityReference(entity_type, entity_id)],
        )
        expected = [
            {
                "entity_type": entity_type.id,
                "entity": entity_id,
            },
        ]
        dump = sut.dump()
        assert isinstance(dump, dict)
        assert expected == dump["featured_entities"]

    def test_dump__with_primary_color(self) -> None:
        hex_value = "#000000"
        sut = RaspberryMintConfiguration(primary_color=hex_value)
        dump = sut.dump()
        assert isinstance(dump, dict)
        assert hex_value == dump["primary_color"]

    def test_dump__with_secondary_color(self) -> None:
        hex_value = "#000000"
        sut = RaspberryMintConfiguration(secondary_color=hex_value)
        dump = sut.dump()
        assert isinstance(dump, dict)
        assert hex_value == dump["secondary_color"]

    def test_dump__with_tertiary_color(self) -> None:
        hex_value = "#000000"
        sut = RaspberryMintConfiguration(tertiary_color=hex_value)
        dump = sut.dump()
        assert isinstance(dump, dict)
        assert hex_value == dump["tertiary_color"]

    def test_get_mutable_instances(self) -> None:
        sut = RaspberryMintConfiguration()
        sut.immutable()
        assert sut.featured_entities.is_immutable
        assert sut.primary_color.is_immutable
        assert sut.secondary_color.is_immutable
        assert sut.tertiary_color.is_immutable
