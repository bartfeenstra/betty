from pathlib import Path

from pytest_mock import MockerFixture
from typing_extensions import override

from betty.app import App
from betty.console.command import Command
from betty.console.command.commands.clear_caches import ClearCaches
from betty.test_utils.console import run
from betty.test_utils.console.command import CommandTestBase


class TestClearCaches(CommandTestBase):
    @override
    def get_sut_class(self) -> type[Command]:
        return ClearCaches

    async def test_configure(
        self, mocker: MockerFixture, new_temporary_app: App, tmp_path: Path
    ) -> None:
        legacy_cache_directory_path = tmp_path / "legacy"
        legacy_cache_directory_path.mkdir()
        mocker.patch(
            "betty.console.command.commands.clear_caches._LEGACY_CACHE_DIRECTORY_PATH",
            legacy_cache_directory_path,
        )
        legacy_cache_item_path = legacy_cache_directory_path / "item"
        legacy_cache_item_path.touch()
        await new_temporary_app.cache.set("KeepMeAroundPlease", "")
        await run(new_temporary_app, "clear-caches")
        async with new_temporary_app.cache.get("KeepMeAroundPlease") as cache_item:
            assert cache_item is None
        assert not legacy_cache_item_path.exists()
