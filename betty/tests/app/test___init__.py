from __future__ import annotations

from json import dumps
from typing import TYPE_CHECKING, Self, override

from babel import Locale

from betty.app import App, AppConfiguration
from betty.factory import Manufacturable
from betty.test_utils.user import StaticUser

if TYPE_CHECKING:
    from pathlib import Path

    from pytest_mock import MockerFixture

    from betty.test_utils.conftest import IsolatedAppFactory


class _Manufacturable(Manufacturable):
    def __init__(self, app: App):
        self.app = app

    @override
    @App.require
    @classmethod
    async def new(cls, app: App, /) -> Self:
        return cls(app)


class TestApp:
    async def test_new(self) -> None:
        locale = Locale("nl", "NL")
        async with await App.new(AppConfiguration(locale=locale)) as sut:
            localizer = await sut.localizer
            assert localizer.locale == locale

    async def test_new_from_environment__without_configuration_file(
        self, mocker: MockerFixture, tmp_path: Path
    ) -> None:
        mocker.patch("betty.app.data.AppConfiguration.FILE", tmp_path / "app.json")
        async with App.new_from_environment():
            pass

    async def test_new_from_environment__with_configuration_file(
        self, mocker: MockerFixture, tmp_path: Path
    ) -> None:
        configuration_file = tmp_path / "app.json"
        with open(tmp_path / "app.json", encoding="utf-8", mode="w") as f:
            f.write(dumps({"locale": "nl-NL"}))
        mocker.patch("betty.app.data.AppConfiguration.FILE", configuration_file)
        async with App.new_from_environment() as sut:
            localizer = await sut.localizer
            assert localizer.locale == Locale("nl", "NL")

    async def test_bootstrap__should_set_user_localizer(
        self, isolated_app_factory: IsolatedAppFactory
    ) -> None:
        user = StaticUser()
        async with isolated_app_factory(user=user) as sut:
            assert sut.user.localizer is await sut.localizer

    async def test_user(self, isolated_app_factory: IsolatedAppFactory) -> None:
        user = StaticUser()
        async with isolated_app_factory(user=user) as sut:
            assert sut.user is user

    async def test_binary_file_cache(self, isolated_app: App) -> None:
        assert isolated_app.binary_file_cache is isolated_app.binary_file_cache

    async def test_cache(self, tmp_path: Path) -> None:
        async with App(cache_directory=tmp_path) as app:
            assert app.cache is app.cache

    async def test_http_client(self, isolated_app: App) -> None:
        assert await isolated_app.http_client is await isolated_app.http_client

    async def test_localizer(self, isolated_app: App) -> None:
        assert await isolated_app.localizer is await isolated_app.localizer

    async def test_localizers(self, isolated_app: App) -> None:
        localizers = await isolated_app.localizers
        assert localizers is await isolated_app.localizers

    async def test_process_pool(self, isolated_app: App) -> None:
        assert isolated_app.process_pool is isolated_app.process_pool
