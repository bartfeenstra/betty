from __future__ import annotations

from typing import Self

from typing_extensions import override

from betty.app import App
from betty.app.factory import AppDependentFactory
from betty.locale import DEFAULT_LOCALE


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

    async def test_spdx_license_repository(self, new_temporary_app: App) -> None:
        async with App.new_temporary() as sut, sut:
            await sut.spdx_license_repository
