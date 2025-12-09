from pathlib import Path

import pytest
from pytest_mock import MockerFixture
from typing_extensions import override

from betty.app import App
from betty.console.command import Command
from betty.console.command.commands.clear_caches import ClearCaches
from betty.plugin import PluginDefinition
from betty.test_utils.console import run
from betty.test_utils.console.command import CommandDefinitionTestBase, CommandTestBase


class TestClearCachesDefinition(CommandDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return ClearCaches.plugin()


class TestClearCaches(CommandTestBase):
    @override
    @pytest.fixture
    def sut(self, isolated_app: App) -> Command:
        return ClearCaches(isolated_app)

    async def test_configure(
        self, mocker: MockerFixture, isolated_app: App, tmp_path: Path
    ) -> None:
        legacy_cache_directory_path = tmp_path / "legacy"
        legacy_cache_directory_path.mkdir()
        mocker.patch(
            "betty.console.command.commands.clear_caches._LEGACY_CACHE_DIRECTORY_PATH",
            legacy_cache_directory_path,
        )
        legacy_cache_item_path = legacy_cache_directory_path / "item"
        legacy_cache_item_path.touch()
        await isolated_app.cache.set("KeepMeAroundPlease", "")
        await run(isolated_app, "clear-caches")
        cache_item = await isolated_app.cache.get("KeepMeAroundPlease")
        assert cache_item is None
        assert not legacy_cache_item_path.exists()
