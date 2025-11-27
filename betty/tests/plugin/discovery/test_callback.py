from __future__ import annotations

from collections.abc import Awaitable, Callable, Collection, Iterable, Sequence
from typing import TYPE_CHECKING, TypeAlias, cast

import pytest

from betty.plugin import PluginDefinition
from betty.plugin.discovery.callback import CallbackDiscovery
from betty.project import Project
from betty.test_utils.plugin import DummyPluginOne

if TYPE_CHECKING:
    from betty.app import App

CallbackResultDiscoveryTestParams: TypeAlias = tuple[
    Collection[PluginDefinition],
    Callable[[], Awaitable[Iterable[PluginDefinition]]]
    | Callable[[], Iterable[PluginDefinition]],
]


class TestCallbackDiscovery:
    @staticmethod
    def _sut_params() -> Sequence[CallbackResultDiscoveryTestParams]:
        async def _async_discovery() -> Iterable[PluginDefinition]:
            return [DummyPluginOne.plugin]

        return [
            ([DummyPluginOne.plugin], lambda: [DummyPluginOne.plugin]),
            ([DummyPluginOne.plugin], _async_discovery),
        ]

    @pytest.fixture(params=_sut_params())
    def sut_params(
        self, request: pytest.FixtureRequest
    ) -> CallbackResultDiscoveryTestParams:
        return cast(CallbackResultDiscoveryTestParams, request.param)

    async def test_discover__global(
        self, sut_params: CallbackResultDiscoveryTestParams
    ) -> None:
        expected, discovery = sut_params
        sut = CallbackDiscovery(discovery)
        assert await sut.discover(None) == expected

    async def test_discover__with_app(
        self, sut_params: CallbackResultDiscoveryTestParams, temporary_app: App
    ) -> None:
        expected, discovery = sut_params
        sut = CallbackDiscovery(discovery)
        assert await sut.discover(temporary_app) == expected

    async def test_discover__with_project(
        self, sut_params: CallbackResultDiscoveryTestParams, temporary_app: App
    ) -> None:
        expected, discovery = sut_params
        async with Project.new_temporary(temporary_app) as project, project:
            sut = CallbackDiscovery(discovery)
            assert await sut.discover(project) == expected
