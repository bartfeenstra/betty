from pathlib import Path

from pytest_mock import MockerFixture

from betty.app import App
from betty.test_utils.console import run


class TestClearCaches:
    async def test_configure(
        self, mocker: MockerFixture, isolated_app: App, tmp_path: Path
    ) -> None:
        legacy_cache_directory_path = tmp_path / "legacy"
        legacy_cache_directory_path.mkdir()
        mocker.patch(
            "betty.plugins.command.clear_caches._LEGACY_CACHE_DIRECTORY_PATH",
            legacy_cache_directory_path,
        )
        legacy_cache_item_path = legacy_cache_directory_path / "item"
        legacy_cache_item_path.touch()
        await isolated_app.cache.set("KeepMeAroundPlease", "")
        await run(isolated_app, "clear-caches")
        cache_item = await isolated_app.cache.get("KeepMeAroundPlease")
        assert cache_item is None
        assert not legacy_cache_item_path.exists()
