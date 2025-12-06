from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from betty.content_provider import ContentProvider, ContentProviderPlugin
from betty.exception import HumanFacingException
from betty.plugin.config import PluginInstanceConfiguration
from betty.project import Project
from betty.project.extension.raspberry_mint import RaspberryMint
from betty.project.extension.raspberry_mint.config import RaspberryMintConfiguration

if TYPE_CHECKING:
    from collections.abc import Mapping

    from betty.app import App
    from betty.data import Path
    from betty.serde.dump import Dump, DumpMapping


class TestRaspberryMintConfiguration:
    async def test_validator__should_validate_featured_entities_configuration(
        self, isolated_app: App, tmp_path: Path
    ) -> None:
        sut = RaspberryMintConfiguration()
        sut.regional_content["unknown-region"] = []
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.enable(RaspberryMint)
            async with project:
                with pytest.raises(HumanFacingException) as exc_info:
                    await project.new_target(sut.validator)
        assert (
            'data["extensions"]["raspberry-mint"]["regional_content"]["unknown-region"]'
            in str(exc_info.value)
        )

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
            ContentProviderPlugin, ContentProvider
        ]("my-first-plugin")
        regional_content = {"front": [content_provider]}
        sut = RaspberryMintConfiguration(regional_content=regional_content)
        assert sut.regional_content["front"][0] is content_provider

    def test_load__with_minimal_configuration(self) -> None:
        dump: Mapping[str, Any] = {}
        RaspberryMintConfiguration().load(dump)

    def test_load__without_dict_should_error(self) -> None:
        dump = None
        with pytest.raises(HumanFacingException):
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

    def test_load__with_regional_content(self) -> None:
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

    def test_dump__with_regional_content(self) -> None:
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

    def test_get_mutables(self) -> None:
        sut = RaspberryMintConfiguration()
        sut.immutable = True
        assert sut.primary_color.immutable
        assert sut.secondary_color.immutable
        assert sut.tertiary_color.immutable
        assert sut.regional_content.immutable
