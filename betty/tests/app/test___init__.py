from __future__ import annotations

import pickle
from typing import Self, TYPE_CHECKING, cast

import pytest
from betty.app import App
from betty.app.factory import AppDependentFactory
from betty.cache.memory import MemoryCache
from betty.locale import DEFAULT_LOCALE
from betty.service import StaticService
from typing_extensions import override

if TYPE_CHECKING:
    from multiprocessing.managers import SyncManager


class TestApp:
    async def test_new_from_environment(self) -> None:
        async with App.new_from_environment() as sut, sut:
            assert sut.cache is sut.cache
            assert await sut.fetcher is await sut.fetcher

    async def test_assets(self) -> None:
        async with App.new_temporary() as sut, sut:
            assert sut.assets is sut.assets

    async def test_binary_file_cache(self) -> None:
        async with App.new_temporary() as sut, sut:
            assert sut.binary_file_cache is sut.binary_file_cache

    async def test_cache(self) -> None:
        async with App.new_temporary() as sut, sut:
            assert sut.cache is sut.cache

    async def test_fetcher(self) -> None:
        async with App.new_temporary() as sut, sut:
            assert await sut.fetcher is await sut.fetcher

    async def test_http_client(self) -> None:
        async with App.new_temporary() as sut, sut:
            assert await sut.http_client is await sut.http_client

    async def test_localizer(self) -> None:
        async with App.new_temporary() as sut, sut:
            assert await sut.localizer is await sut.localizer

    async def test_localizers(self) -> None:
        async with App.new_temporary() as sut, sut:
            localizer = sut.localizers
            assert localizer is sut.localizers
            assert (await localizer.get(DEFAULT_LOCALE)).locale == DEFAULT_LOCALE

    async def test_process_pool(self) -> None:
        async with App.new_temporary() as sut, sut:
            assert sut.process_pool is sut.process_pool

    async def test_new_target(self) -> None:
        class Dependent:
            pass

        async with App.new_temporary() as sut, sut:
            await sut.new_target(Dependent)

    async def test_new_with_app_dependent_factory(self) -> None:
        class Dependent(AppDependentFactory):
            def __init__(self, app: App):
                self.app = app

            @override
            @classmethod
            async def new_for_app(cls, app: App) -> Self:
                return cls(app)

        async with App.new_temporary() as sut, sut:
            dependent = await sut.new_target(Dependent)
            assert dependent.app is sut

    async def test_spdx_license_repository(self) -> None:
        async with App.new_temporary() as sut, sut:
            await sut.spdx_license_repository

    async def test___getstate___not_yet_bootstrapped_should_error(self) -> None:
        async with App.new_temporary() as sut:
            with pytest.raises(RuntimeError):
                pickle.loads(pickle.dumps(sut))

    async def test___getstate___minimal(self) -> None:
        async with App.new_temporary() as sut, sut:
            unpickled_sut = pickle.loads(pickle.dumps(sut))

        await unpickled_sut.shutdown()

    async def test___getstate___full(
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
            unpickled_sut.assets  # noqa B018
            await unpickled_sut.localizer
            unpickled_sut.localizers  # noqa B018
            await unpickled_sut.http_client
            await unpickled_sut.fetcher
            unpickled_sut.process_pool  # noqa B018
            unpickled_sut.multiprocessing_manager  # noqa B018
            await unpickled_sut.spdx_license_repository

            await unpickled_sut.shutdown()
