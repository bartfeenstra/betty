from __future__ import annotations

from typing import TYPE_CHECKING, Self

from typing_extensions import override

from betty.app import App
from betty.app.factory import AppDependentFactory, AppDependentSelfFactory
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.project import Project
from betty.requirement import Requirement
from betty.test_utils.plugin import DummyPluginDefinition
from betty.test_utils.user import StaticUser

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


class TestApp:
    async def test_requires__with_global(self) -> None:
        subject = "My First Subject"
        requires = await App.requires(None, subject)
        assert isinstance(requires, Requirement)
        assert subject in requires.localize(DEFAULT_LOCALIZER)

    async def test_requires__with_app(self, isolated_app: App) -> None:
        assert await App.requires(isolated_app, "") is isolated_app

    async def test_requires__with_project(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            assert await App.requires(project, "") is isolated_app

    async def test_plugins(self, isolated_app: App) -> None:
        await isolated_app.plugins(DummyPluginDefinition)

    async def test_new_from_environment(self, isolated_app: App) -> None:
        assert isolated_app.cache is isolated_app.cache

    async def test_bootstrap__should_set_user_localizer(
        self, mocker: MockerFixture, isolated_app: App
    ) -> None:
        user = StaticUser()
        async with App.new_isolated(user=user) as sut, sut:
            assert sut.user.localizer is await sut.localizer

    async def test_user(self, isolated_app: App) -> None:
        user = StaticUser()
        async with App.new_isolated(user=user) as sut, sut:
            assert sut.user is user

    async def test_assets(self, isolated_app: App) -> None:
        assert isolated_app.assets is isolated_app.assets

    async def test_binary_file_cache(self, isolated_app: App) -> None:
        assert isolated_app.binary_file_cache is isolated_app.binary_file_cache

    async def test_cache(self, isolated_app: App) -> None:
        assert isolated_app.cache is isolated_app.cache

    async def test_http_client(self, isolated_app: App) -> None:
        assert await isolated_app.http_client is await isolated_app.http_client

    async def test_localizer(self, isolated_app: App) -> None:
        assert await isolated_app.localizer is await isolated_app.localizer

    async def test_localizers(self, isolated_app: App) -> None:
        localizers = await isolated_app.localizers
        assert localizers is await isolated_app.localizers

    async def test_process_pool(self, isolated_app: App) -> None:
        assert isolated_app.process_pool is isolated_app.process_pool

    async def test_new_target(self, isolated_app: App) -> None:
        class Dependent:
            pass

        await isolated_app.new_target(Dependent)

    async def test_new_target__with_app_dependent_factory(
        self, isolated_app: App
    ) -> None:
        class _Factory(AppDependentFactory[App]):
            @override
            async def new_for_app(self, app: App, /) -> App:
                return app

        target = await isolated_app.new_target(_Factory())
        assert target is isolated_app

    async def test_new_target__with_app_dependent_self_factory(
        self, isolated_app: App
    ) -> None:
        class Dependent(AppDependentSelfFactory):
            def __init__(self, app: App):
                self.app = app

            @override
            @classmethod
            async def new_for_app(cls, app: App, /) -> Self:
                return cls(app)

        dependent = await isolated_app.new_target(Dependent)
        assert dependent.app is isolated_app

    async def test__spdx_license_repository(self, isolated_app: App) -> None:
        await isolated_app._spdx_license_repository
