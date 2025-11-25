from __future__ import annotations

from collections.abc import Awaitable, Callable, Collection, Iterable, Sequence
from typing import TypeAlias, cast

import pytest

from betty.app import App
from betty.plugin import PluginDefinition
from betty.plugin.discovery.app import AppDiscovery
from betty.project import Project
from betty.test_utils.plugin import DummyPluginOne

AppDiscoveryTestParams: TypeAlias = tuple[
    Collection[PluginDefinition],
    Callable[[App], Awaitable[Iterable[PluginDefinition]]]
    | Callable[[App], Iterable[PluginDefinition]],
]


class TestAppDiscovery:
    @staticmethod
    def _sut_params() -> Sequence[AppDiscoveryTestParams]:
        async def _async_discovery(app: App) -> Iterable[PluginDefinition]:
            return [DummyPluginOne]

        return [
            ([DummyPluginOne], lambda app: [DummyPluginOne]),
            ([DummyPluginOne], _async_discovery),
        ]

    @pytest.fixture(params=_sut_params())
    def sut_params(self, request: pytest.FixtureRequest) -> AppDiscoveryTestParams:
        return cast(AppDiscoveryTestParams, request.param)

    async def test_discover_global(self, sut_params: AppDiscoveryTestParams) -> None:
        expected, discovery = sut_params
        sut = AppDiscovery(discovery)
        assert not list(await sut.discover(None))

    async def test_discover__with_app(
        self, sut_params: AppDiscoveryTestParams, temporary_app: App
    ) -> None:
        expected, discovery = sut_params
        sut = AppDiscovery(discovery)
        assert await sut.discover(temporary_app) == expected

    async def test_discover__with_project(
        self, sut_params: AppDiscoveryTestParams, temporary_app: App
    ) -> None:
        expected, discovery = sut_params
        async with Project.new_temporary(temporary_app) as project, project:
            sut = AppDiscovery(discovery)
            assert await sut.discover(project) == expected
