from __future__ import annotations

from typing import Self

from typing_extensions import override

from betty.app import App
from betty.app.factory import AppDependentFactory


class TestApp:
    async def test_localizer(self) -> None:
        async with App.new_temporary() as sut, sut:
            assert await sut.localizer is not None

    async def test_http_client(self) -> None:
        async with App.new_temporary() as sut, sut:
            assert await sut.http_client is not None

    async def test_fetcher(self) -> None:
        async with App.new_temporary() as sut, sut:
            assert await sut.fetcher is not None

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
