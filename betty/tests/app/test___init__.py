from __future__ import annotations

from typing import Self
from typing_extensions import override

from betty.app import App
from betty.app.factory import AppDependentFactory


class TestApp:
    async def test_fetcher(self) -> None:
        async with App.new_temporary() as sut, sut:
            assert sut.fetcher is not None

    async def test_new_dependent(self) -> None:
        class Dependent:
            pass

        async with App.new_temporary() as sut, sut:
            sut.new_dependent(Dependent)

    async def test_new_dependent_with_app_dependent_factory(self) -> None:
        class Dependent(AppDependentFactory):
            def __init__(self, app: App):
                self.app = app

            @override
            @classmethod
            def new_for_app(cls, app: App) -> Self:
                return cls(app)

        async with App.new_temporary() as sut, sut:
            dependent = sut.new_dependent(Dependent)
            assert dependent.app is sut
