from __future__ import annotations

from typing import TYPE_CHECKING, Self

from typing_extensions import override

from betty.app import App
from betty.app.factory import AppDependentFactory
from betty.test_utils.user import StaticUser

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


class TestApp:
    async def test_new_from_environment(self, temporary_app: App) -> None:
        async with App.new_from_environment() as sut, sut:
            assert sut.cache is sut.cache

    async def test_bootstrap__should_set_user_localizer(
        self, mocker: MockerFixture, temporary_app: App
    ) -> None:
        user = StaticUser()
        async with App.new_temporary(user=user) as sut, sut:
            assert sut.user.localizer is await sut.localizer

    async def test_user(self, temporary_app: App) -> None:
        user = StaticUser()
        async with App.new_temporary(user=user) as sut, sut:
            assert sut.user is user

    async def test_assets(self, temporary_app: App) -> None:
        assert temporary_app.assets is temporary_app.assets

    async def test_binary_file_cache(self, temporary_app: App) -> None:
        assert temporary_app.binary_file_cache is temporary_app.binary_file_cache

    async def test_cache(self, temporary_app: App) -> None:
        assert temporary_app.cache is temporary_app.cache

    async def test_http_rate_limit_repository(self, temporary_app: App) -> None:
        assert list(temporary_app.http_rate_limit_repository)

    async def test_http_client(self, temporary_app: App) -> None:
        assert await temporary_app.http_client is await temporary_app.http_client

    async def test_localizer(self, temporary_app: App) -> None:
        assert await temporary_app.localizer is await temporary_app.localizer

    async def test_localizers(self, temporary_app: App) -> None:
        localizers = await temporary_app.localizers
        assert localizers is await temporary_app.localizers

    async def test_process_pool(self, temporary_app: App) -> None:
        assert temporary_app.process_pool is temporary_app.process_pool

    async def test_new_target(self, temporary_app: App) -> None:
        class Dependent:
            pass

        await temporary_app.new_target(Dependent)

    async def test_new_target__with_app_dependent_factory(
        self, temporary_app: App
    ) -> None:
        class Dependent(AppDependentFactory):
            def __init__(self, app: App):
                self.app = app

            @override
            @classmethod
            async def new_for_app(cls, app: App) -> Self:
                return cls(app)

        dependent = await temporary_app.new_target(Dependent)
        assert dependent.app is temporary_app

    async def test_spdx_license_repository(self, temporary_app: App) -> None:
        await temporary_app.spdx_license_repository
