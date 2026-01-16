from __future__ import annotations

import pickle
from typing import TYPE_CHECKING, Self, cast

import pytest
from typing_extensions import override

from betty.app import App
from betty.app.factory import AppDependentFactory
from betty.cache.memory import MemoryCache
from betty.locale import DEFAULT_LOCALE
from betty.service import StaticService

if TYPE_CHECKING:
    from multiprocessing.managers import SyncManager


class TestApp:
    async def test_new_from_environment(self, new_temporary_app: App) -> None:
        async with App.new_from_environment() as sut, sut:
            assert sut.cache is sut.cache
            assert await sut.fetcher is await sut.fetcher

    async def test_assets(self, new_temporary_app: App) -> None:
        assert new_temporary_app.assets is new_temporary_app.assets

    async def test_binary_file_cache(self, new_temporary_app: App) -> None:
        assert (
            new_temporary_app.binary_file_cache is new_temporary_app.binary_file_cache
        )

    async def test_cache(self, new_temporary_app: App) -> None:
        assert new_temporary_app.cache is new_temporary_app.cache

    async def test_fetcher(self, new_temporary_app: App) -> None:
        assert await new_temporary_app.fetcher is await new_temporary_app.fetcher

    async def test_http_client(self, new_temporary_app: App) -> None:
        assert (
            await new_temporary_app.http_client is await new_temporary_app.http_client
        )

    async def test_localizer(self, new_temporary_app: App) -> None:
        assert await new_temporary_app.localizer is await new_temporary_app.localizer

    async def test_localizers(self, new_temporary_app: App) -> None:
        localizer = new_temporary_app.localizers
        assert localizer is new_temporary_app.localizers
        assert (await localizer.get(DEFAULT_LOCALE)).locale == DEFAULT_LOCALE

    async def test_process_pool(self, new_temporary_app: App) -> None:
        assert new_temporary_app.process_pool is new_temporary_app.process_pool

    async def test_new_target(self, new_temporary_app: App) -> None:
        class Dependent:
            pass

        await new_temporary_app.new_target(Dependent)

    async def test_new_target__with_app_dependent_factory(
        self, new_temporary_app: App
    ) -> None:
        class Dependent(AppDependentFactory):
            def __init__(self, app: App):
                self.app = app

            @override
            @classmethod
            async def new_for_app(cls, app: App) -> Self:
                return cls(app)

        dependent = await new_temporary_app.new_target(Dependent)
        assert dependent.app is new_temporary_app

    async def test_spdx_license_repository(self, new_temporary_app: App) -> None:
        await new_temporary_app.spdx_license_repository

    async def test___getstate____not_yet_bootstrapped_should_error(self) -> None:
        async with App.new_temporary() as sut:
            with pytest.raises(RuntimeError):
                pickle.loads(pickle.dumps(sut))

    async def test___getstate____minimal(self, new_temporary_app: App) -> None:
        unpickled_sut = pickle.loads(pickle.dumps(new_temporary_app))
        await unpickled_sut.shutdown()

    async def test___getstate____full(
        self, multiprocessing_manager: SyncManager
    ) -> None:
        async with (
            App.new_temporary(
                cache_factory=StaticService(
                    MemoryCache(manager=multiprocessing_manager)
                )
            ) as sut,
            sut,
        ):
            unpickled_sut = cast(App, pickle.loads(pickle.dumps(sut)))

            # Test the cache.
            cache_item_id = "my-first-cache-item-id"
            cache_item_value = "My first cache item"
            cache = sut.cache
            unpickled_cache = unpickled_sut.cache
            await cache.set(cache_item_id, cache_item_value)
            async with unpickled_cache.get(cache_item_id) as cache_item:
                assert cache_item
                assert await cache_item.value() == cache_item_value

            # Test the binary file cache.
            binary_file_cache_item_id = "my-first-cache-item-id"
            binary_file_cache_item_value = b"My first cache item"
            binary_file_cache = sut.binary_file_cache
            unpickled_binary_file_cache = unpickled_sut.binary_file_cache
            await binary_file_cache.set(
                binary_file_cache_item_id, binary_file_cache_item_value
            )
            async with unpickled_binary_file_cache.get(
                binary_file_cache_item_id
            ) as cache_item:
                assert cache_item
                assert await cache_item.value() == binary_file_cache_item_value

            # Test that other services can be requested.
            unpickled_sut.assets  # noqa: B018
            await unpickled_sut.localizer
            unpickled_sut.localizers  # noqa: B018
            await unpickled_sut.http_client
            await unpickled_sut.fetcher
            unpickled_sut.process_pool  # noqa: B018
            unpickled_sut.multiprocessing_manager  # noqa: B018
            await unpickled_sut.spdx_license_repository

        await unpickled_sut.shutdown()
