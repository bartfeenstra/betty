from __future__ import annotations

from typing import TYPE_CHECKING, Self

from typing_extensions import override

from betty.app import App
from betty.app.factory import require_app
from betty.locale.localize import DEFAULT_LOCALIZER
from betty.project import Project
from betty.requirement import Requirement
from betty.service.level.factory import ServiceLevelDependentSelfFactory
from betty.service.level.universal import universe
from betty.test_utils.plugin import DummyPluginDefinition
from betty.test_utils.user import StaticUser

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


class _ServiceLevelDependentSelfFactory(ServiceLevelDependentSelfFactory):
    def __init__(self, app: App):
        self.app = app

    @override
    @classmethod
    @require_app
    async def new_for_services(cls, app: App, /) -> Self:
        return cls(app)


class TestApp:
    async def test_requires__with_universe(self) -> None:
        subject = "My First Subject"
        requires = await App.requires(universe, subject)
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

    async def test__spdx_license_repository(self, isolated_app: App) -> None:
        await isolated_app._spdx_license_repository
