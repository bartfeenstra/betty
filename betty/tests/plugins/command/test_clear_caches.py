from pathlib import Path

from pytest_mock import MockerFixture

from betty.cache.memory import MemoryCache
from betty.test_utils.conftest import IsolatedAppFactory
from betty.test_utils.console import run
from betty.test_utils.user import StaticUser


class TestClearCaches:
    async def test_configure__without_confirmation(
        self,
        mocker: MockerFixture,
        isolated_app_factory: IsolatedAppFactory,
        tmp_path: Path,
    ) -> None:
        legacy_cache_directory_path = tmp_path / "legacy"
        legacy_cache_directory_path.mkdir()
        mocker.patch(
            "betty.plugins.command.clear_caches._LEGACY_CACHE_DIRECTORY_PATH",
            legacy_cache_directory_path,
        )
        legacy_cache_item_path = legacy_cache_directory_path / "item"
        legacy_cache_item_path.touch()

        user = StaticUser(confirmations=[False])

        async with isolated_app_factory(cache=MemoryCache(), user=user) as app:
            await app.cache.set("KeepMeAroundPlease", "")
            await run(app, "clear-caches")
            cache_item = await app.cache.get("KeepMeAroundPlease")
            assert cache_item is not None
            assert legacy_cache_item_path.exists()

    async def test_configure__with_confirmation(
        self,
        mocker: MockerFixture,
        isolated_app_factory: IsolatedAppFactory,
        tmp_path: Path,
    ) -> None:
        legacy_cache_directory_path = tmp_path / "legacy"
        legacy_cache_directory_path.mkdir()
        mocker.patch(
            "betty.plugins.command.clear_caches._LEGACY_CACHE_DIRECTORY_PATH",
            legacy_cache_directory_path,
        )
        legacy_cache_item_path = legacy_cache_directory_path / "item"
        legacy_cache_item_path.touch()

        user = StaticUser(confirmations=[True])

        async with isolated_app_factory(cache=MemoryCache(), user=user) as app:
            await app.cache.set("KeepMeAroundPlease", "")
            await run(app, "clear-caches")
            cache_item = await app.cache.get("KeepMeAroundPlease")
            assert cache_item is None
            assert not legacy_cache_item_path.exists()

    async def test_configure__with_yes(
        self,
        mocker: MockerFixture,
        isolated_app_factory: IsolatedAppFactory,
        tmp_path: Path,
    ) -> None:
        legacy_cache_directory_path = tmp_path / "legacy"
        legacy_cache_directory_path.mkdir()
        mocker.patch(
            "betty.plugins.command.clear_caches._LEGACY_CACHE_DIRECTORY_PATH",
            legacy_cache_directory_path,
        )
        legacy_cache_item_path = legacy_cache_directory_path / "item"
        legacy_cache_item_path.touch()
        async with isolated_app_factory(cache=MemoryCache()) as app:
            await app.cache.set("KeepMeAroundPlease", "")
            await run(app, "clear-caches", "--yes")
            cache_item = await app.cache.get("KeepMeAroundPlease")
            assert cache_item is None
            assert not legacy_cache_item_path.exists()
