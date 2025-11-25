from __future__ import annotations

from collections.abc import Awaitable, Callable, Collection, Iterable, Sequence
from typing import TYPE_CHECKING, TypeAlias, cast

import pytest

from betty.plugin import PluginDefinition
from betty.plugin.discovery.project import ProjectDiscovery
from betty.project import Project
from betty.test_utils.plugin import DummyPluginOne

if TYPE_CHECKING:
    from betty.app import App

ProjectDiscoveryTestParams: TypeAlias = tuple[
    Collection[PluginDefinition],
    Callable[[Project], Awaitable[Iterable[PluginDefinition]]]
    | Callable[[Project], Iterable[PluginDefinition]],
]


class TestProjectDiscovery:
    @staticmethod
    def _sut_params() -> Sequence[ProjectDiscoveryTestParams]:
        async def _async_discovery(project: Project) -> Iterable[PluginDefinition]:
            return [DummyPluginOne]

        return [
            ([DummyPluginOne], lambda project: [DummyPluginOne]),
            ([DummyPluginOne], _async_discovery),
        ]

    @pytest.fixture(params=_sut_params())
    def sut_params(self, request: pytest.FixtureRequest) -> ProjectDiscoveryTestParams:
        return cast(ProjectDiscoveryTestParams, request.param)

    async def test_discover_global(
        self, sut_params: ProjectDiscoveryTestParams
    ) -> None:
        expected, discovery = sut_params
        sut = ProjectDiscovery(discovery)
        assert not list(await sut.discover(None))

    async def test_discover__with_app(
        self,
        sut_params: ProjectDiscoveryTestParams,
        temporary_app: App,
    ) -> None:
        expected, discovery = sut_params
        sut = ProjectDiscovery(discovery)
        assert not list(await sut.discover(temporary_app))

    async def test_discover__with_project(
        self,
        sut_params: ProjectDiscoveryTestParams,
        temporary_app: App,
    ) -> None:
        expected, discovery = sut_params
        async with Project.new_temporary(temporary_app) as project, project:
            sut = ProjectDiscovery(discovery)
            assert await sut.discover(project) == expected
