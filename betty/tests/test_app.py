from __future__ import annotations

from json import dumps
from typing import TYPE_CHECKING, Self, override

from babel import Locale

from betty.app import App, AppData
from betty.factory import Arg1Manufacturable
from betty.test_utils.data import DataTestBase
from betty.test_utils.user import StaticUser

if TYPE_CHECKING:
    from pathlib import Path

    from pytest_mock import MockerFixture

    from betty.test_utils.conftest import IsolatedAppFactory


class _ServiceLevel_Manufacturable(Arg1Manufacturable):
    def __init__(self, app: App, /):
        self.app = app

    @override
    @App.require
    @classmethod
    async def new(cls, app: App, /) -> Self:
        return cls(app)


class TestApp:
    async def test_new_from_environment__without_configuration_file(
        self, mocker: MockerFixture, tmp_path: Path
    ) -> None:
        mocker.patch("betty.app.AppData.FILE", tmp_path / "app.json")
        async with App.new_from_environment():
            pass

    async def test_new_from_environment__with_configuration_file(
        self, mocker: MockerFixture, tmp_path: Path
    ) -> None:
        configuration_file = tmp_path / "app.json"
        with open(tmp_path / "app.json", encoding="utf-8", mode="w") as f:
            f.write(dumps({"locale": "nl-NL"}))
        mocker.patch("betty.app.AppData.FILE", configuration_file)
        async with App.new_from_environment() as sut:
            assert sut.user.localizer.locale == Locale("nl", "NL")

    async def test_user(self, isolated_app_factory: IsolatedAppFactory) -> None:
        user = StaticUser()
        async with isolated_app_factory(user=user) as sut:
            assert sut.user is user

    async def test_http_client(self, isolated_app: App) -> None:
        assert await isolated_app.http_client is await isolated_app.http_client

    async def test_localizers(self, isolated_app: App) -> None:
        assert isolated_app.localizers is isolated_app.localizers

    async def test_process_pool(self, isolated_app: App) -> None:
        assert isolated_app.process_pool is isolated_app.process_pool

    async def test_asset_directories(self, isolated_app: App) -> None:
        assert isolated_app.asset_directories is isolated_app.asset_directories

    async def test_binary_file_cache(self, isolated_app: App) -> None:
        assert isolated_app.binary_file_cache is isolated_app.binary_file_cache

    async def test_cache(self, isolated_app: App) -> None:
        assert isolated_app.cache is isolated_app.cache

    async def test_media_types(self, isolated_app: App) -> None:
        assert isolated_app.media_types is isolated_app.media_types

    async def test_rate_limits(self, isolated_app: App) -> None:
        assert isolated_app.rate_limits is isolated_app.rate_limits

    async def test_serializers(self, isolated_app: App) -> None:
        assert isolated_app.serializers is isolated_app.serializers


class TestAppData(DataTestBase[AppData]):
    sut_cls = AppData

    def test___init____minimal_locale(self) -> None:
        sut = AppData()
        assert sut.locale is None

    def test___init____with_locale(self) -> None:
        locale = Locale("nl", "NL")
        sut = AppData(locale=locale)
        assert sut.locale is locale

    def test_locale(self) -> None:
        sut = AppData()
        locale = Locale("nl", "NL")
        sut.locale = locale
        assert sut.locale is locale
