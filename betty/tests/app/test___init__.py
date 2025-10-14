from __future__ import annotations

from typing import TYPE_CHECKING, Self

from typing_extensions import override

from betty.app import App
from betty.app.factory import AppDependentFactory
from betty.test_utils.user import StaticUser

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


class TestApp:
    async def test_new_from_environment(self, new_temporary_app: App) -> None:
        async with App.new_from_environment() as sut, sut:
            assert sut.cache is sut.cache

    async def test_bootstrap__should_set_user_localizer(
        self, mocker: MockerFixture, new_temporary_app: App
    ) -> None:
        user = StaticUser()
        async with App.new_temporary(user=user) as sut, sut:
            assert sut.user.localizer is await sut.localizer

    async def test_user(self, new_temporary_app: App) -> None:
        user = StaticUser()
        async with App.new_temporary(user=user) as sut, sut:
            assert sut.user is user

    async def test_assets(self, new_temporary_app: App) -> None:
        assert new_temporary_app.assets is new_temporary_app.assets

    async def test_binary_file_cache(self, new_temporary_app: App) -> None:
        assert (
            new_temporary_app.binary_file_cache is new_temporary_app.binary_file_cache
        )

    async def test_cache(self, new_temporary_app: App) -> None:
        assert new_temporary_app.cache is new_temporary_app.cache

    async def test_http_rate_limit_repository(self, new_temporary_app: App) -> None:
        assert list(new_temporary_app.http_rate_limit_repository)

    async def test_http_client(self, new_temporary_app: App) -> None:
        assert (
            await new_temporary_app.http_client is await new_temporary_app.http_client
        )

    async def test_localizer(self, new_temporary_app: App) -> None:
        assert await new_temporary_app.localizer is await new_temporary_app.localizer

    async def test_localizers(self, new_temporary_app: App) -> None:
        localizers = await new_temporary_app.localizers
        assert localizers is await new_temporary_app.localizers

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
