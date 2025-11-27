from __future__ import annotations

import pytest

from betty.content_provider import ContentProvider, ContentProviderPlugin
from betty.exception import HumanFacingException
from betty.plugin.config import PluginInstanceConfiguration
from betty.project.extension.theme.config import RegionalContentConfiguration


class TestRegionalContentConfiguration:
    def test___getitem__(self) -> None:
        sut = RegionalContentConfiguration()
        assert sut["front"] is sut["front"]

    def test___setitem__(self) -> None:
        sut = RegionalContentConfiguration()
        content_provider = PluginInstanceConfiguration[
            ContentProviderPlugin, ContentProvider
        ]("my-first-plugin")
        sut["front"] = [content_provider]
        assert sut["front"][0] is content_provider

    def test_dump__without_regions(self) -> None:
        sut = RegionalContentConfiguration()
        actual = sut.dump()
        assert actual == {}

    def test_dump__with_empty_regions(self) -> None:
        sut = RegionalContentConfiguration()
        sut["front"]
        actual = sut.dump()
        assert actual == {}

    def test_dump__with_full_regions(self) -> None:
        sut = RegionalContentConfiguration()
        sut["front"].append(PluginInstanceConfiguration("my-first-plugin"))
        actual = sut.dump()
        assert actual == {
            "front": [
                "my-first-plugin",
            ],
        }

    def test_load__without_regions(self) -> None:
        sut = RegionalContentConfiguration()
        with pytest.raises(HumanFacingException):
            sut.load({})

    def test_load__with_empty_regions(self) -> None:
        sut = RegionalContentConfiguration()
        with pytest.raises(HumanFacingException):
            sut.load(
                {
                    "front": [],
                }
            )

    def test_load__with_full_regions(self) -> None:
        sut = RegionalContentConfiguration()
        sut.load(
            {
                "front": [
                    "my-first-plugin",
                ],
            }
        )
        assert sut["front"][0].id == "my-first-plugin"

    def test_validate__with_unknown_region(self) -> None:
        sut = RegionalContentConfiguration(
            {
                "non-existent-region": [
                    PluginInstanceConfiguration("my-first-plugin"),
                ],
            }
        )
        with pytest.raises(HumanFacingException):
            sut.validate([])
