from __future__ import annotations

from collections.abc import Awaitable, Callable, Collection, Iterable, Sequence
from typing import TYPE_CHECKING, TypeAlias, cast

import pytest

from betty.plugin import PluginDefinition
from betty.plugin.discovery.extension import ExtensionDiscovery
from betty.project import Project
from betty.project.extension import Extension, ExtensionDefinition
from betty.test_utils.plugin import DUMMY_PLUGIN_ONE
from betty.test_utils.project.extension import DummyExtension

if TYPE_CHECKING:
    from betty.app import App

ExtensionDiscoveryTestParams: TypeAlias = tuple[
    Collection[PluginDefinition],
    Callable[[Extension], Awaitable[Iterable[PluginDefinition]]]
    | Callable[[Extension], Iterable[PluginDefinition]],
]


class TestExtensionDiscovery:
    @staticmethod
    def _sut_params() -> Sequence[ExtensionDiscoveryTestParams]:
        async def _async_discovery(project: Extension) -> Iterable[PluginDefinition]:
            return [DUMMY_PLUGIN_ONE]

        return [
            ([DUMMY_PLUGIN_ONE], lambda project: [DUMMY_PLUGIN_ONE]),
            ([DUMMY_PLUGIN_ONE], _async_discovery),
        ]

    @pytest.fixture(params=_sut_params())
    def sut_params(
        self, request: pytest.FixtureRequest
    ) -> ExtensionDiscoveryTestParams:
        return cast(ExtensionDiscoveryTestParams, request.param)

    async def test_discover_global(
        self, sut_params: ExtensionDiscoveryTestParams
    ) -> None:
        expected, discovery = sut_params
        sut = ExtensionDiscovery(DummyExtension, discovery)
        assert not list(await sut.discover(None))

    async def test_discover__with_app(
        self,
        sut_params: ExtensionDiscoveryTestParams,
        temporary_app: App,
    ) -> None:
        expected, discovery = sut_params
        sut = ExtensionDiscovery(DummyExtension, discovery)
        assert not list(await sut.discover(temporary_app))

    async def test_discover__with_project_without_extension(
        self,
        sut_params: ExtensionDiscoveryTestParams,
        temporary_app: App,
    ) -> None:
        expected, discovery = sut_params
        async with Project.new_temporary(temporary_app) as project, project:
            sut = ExtensionDiscovery(DummyExtension, discovery)
            assert not list(await sut.discover(project))

    async def test_discover__with_project_with_extension(
        self,
        sut_params: ExtensionDiscoveryTestParams,
        temporary_app: App,
    ) -> None:
        expected, discovery = sut_params
        with ExtensionDefinition.type.override_discovery(DummyExtension.plugin):
            async with Project.new_temporary(temporary_app) as project:
                project.configuration.extensions.enable(DummyExtension)
                async with project:
                    sut = ExtensionDiscovery(DummyExtension, discovery)
                    assert await sut.discover(project) == expected
