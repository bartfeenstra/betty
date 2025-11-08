from __future__ import annotations

from typing import TYPE_CHECKING, Any

from betty.content_provider import ContentProvider, ContentProviderDefinition
from betty.exception import HumanFacingException
from betty.plugin.config import PluginInstanceConfiguration
from betty.project.extension.raspberry_mint.config import RaspberryMintConfiguration
from betty.test_utils.exception import raises_error

if TYPE_CHECKING:
    from collections.abc import Mapping

    from betty.serde.dump import Dump, DumpMapping


class TestRaspberryMintConfiguration:
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

    def test_regional_content__from___init__(self) -> None:
        content_provider = PluginInstanceConfiguration[
            ContentProviderDefinition, ContentProvider
        ]("my-first-plugin")
        content = {"front": [content_provider]}
        sut = RaspberryMintConfiguration(content=content)
        assert sut.regional_content["front"][0] is content_provider

    def test_load__with_minimal_configuration(self) -> None:
        dump: Mapping[str, Any] = {}
        RaspberryMintConfiguration().load(dump)

    def test_load__without_dict_should_error(self) -> None:
        dump = None
        with raises_error(error_type=HumanFacingException):
            RaspberryMintConfiguration().load(dump)

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

    def test_load__with_content(self) -> None:
        sut = RaspberryMintConfiguration()
        sut.load(
            {
                "regional_content": {
                    "front": [
                        "my-first-plugin",
                    ],
                }
            }
        )
        assert sut.regional_content["front"][0].id == "my-first-plugin"

    def test_dump__with_minimal_configuration(self) -> None:
        sut = RaspberryMintConfiguration()
        expected: DumpMapping[Dump] = {
            "primary_color": RaspberryMintConfiguration.DEFAULT_PRIMARY_COLOR,
            "secondary_color": RaspberryMintConfiguration.DEFAULT_SECONDARY_COLOR,
            "tertiary_color": RaspberryMintConfiguration.DEFAULT_TERTIARY_COLOR,
        }
        assert sut.dump() == expected

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

    def test_dump__with_content(self) -> None:
        sut = RaspberryMintConfiguration()
        sut.regional_content["front"].append(
            PluginInstanceConfiguration("my-first-plugin")
        )
        actual = sut.dump()
        assert actual["regional_content"] == {
            "front": [
                "my-first-plugin",
            ],
        }

    def test_get_mutable_instances(self) -> None:
        sut = RaspberryMintConfiguration()
        sut.immutable()
        assert sut.primary_color.is_immutable
        assert sut.secondary_color.is_immutable
        assert sut.tertiary_color.is_immutable
        assert sut.regional_content.is_immutable
