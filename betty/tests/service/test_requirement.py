from collections.abc import Awaitable, Callable
from typing import TypeAlias, Unpack

import pytest

from betty.app import App
from betty.extension import ExtensionDefinition
from betty.plugin.discovery.static import StaticDiscovery
from betty.project import Project
from betty.requirement import UnmetRequirement
from betty.service.level.universal import universe
from betty.service.requirement import (
    ServiceLevelKwargs,
    require_app,
    require_extension,
    require_project,
)
from betty.test_utils.project.extension import DummyExtensionOne


@require_app
def _require_app_target_sync(*, app: App) -> App:
    return app


@require_app
async def _require_app_target_async(*, app: App) -> App:
    return app


class _RequireAppTargetClassMethod:
    @classmethod
    @require_app
    async def target(cls, *, app: App) -> App:
        return app


class _RequireAppTargetInstanceMethod:
    @require_app
    async def target(self, *, app: App) -> App:
        return app


_test_require_app_targets = pytest.mark.parametrize(
    "target",
    [
        _require_app_target_sync,
        _require_app_target_async,
        _RequireAppTargetClassMethod.target,
        _RequireAppTargetInstanceMethod().target,
    ],
)

_TestRequireAppTarget: TypeAlias = Callable[
    [Unpack[ServiceLevelKwargs]], Awaitable[App]
]


@_test_require_app_targets
async def test_require_app__with_universe(target: _TestRequireAppTarget) -> None:
    with pytest.raises(UnmetRequirement):
        await target(services=universe)


@_test_require_app_targets
async def test_require_app__with_app(
    isolated_app: App, target: _TestRequireAppTarget
) -> None:
    assert await target(services=isolated_app) is isolated_app


@_test_require_app_targets
async def test_require_app__with_project(
    isolated_app: App, target: _TestRequireAppTarget
) -> None:
    async with Project.new_isolated(isolated_app) as project, project:
        assert await target(services=project) is isolated_app


@require_project
def _require_project_target_sync(*, project: Project) -> Project:
    return project


@require_project
async def _require_project_target_async(*, project: Project) -> Project:
    return project


class _RequireProjectTargetClassMethod:
    @classmethod
    @require_project
    async def target(cls, *, project: Project) -> Project:
        return project


class _RequireProjectTargetInstanceMethod:
    @require_project
    async def target(self, *, project: Project) -> Project:
        return project


_test_require_project_targets = pytest.mark.parametrize(
    "target",
    [
        _require_project_target_sync,
        _require_project_target_async,
        _RequireProjectTargetClassMethod.target,
        _RequireProjectTargetInstanceMethod().target,
    ],
)

_TestRequireProjectTarget: TypeAlias = Callable[
    [Unpack[ServiceLevelKwargs]], Awaitable[Project]
]


@_test_require_project_targets
async def test_require_project__with_universe(
    target: _TestRequireProjectTarget,
) -> None:
    with pytest.raises(UnmetRequirement):
        await target(services=universe)


@_test_require_project_targets
async def test_require_project__with_app(
    isolated_app: App, target: _TestRequireProjectTarget
) -> None:
    with pytest.raises(UnmetRequirement):
        await target(services=isolated_app)


@_test_require_project_targets
async def test_require_project__with_project(
    isolated_app: App, target: _TestRequireProjectTarget
) -> None:
    async with Project.new_isolated(isolated_app) as project, project:
        assert await target(services=project) is project


@require_extension(DummyExtensionOne)
def _require_extension_target_sync(
    *, extension: DummyExtensionOne
) -> DummyExtensionOne:
    return extension


@require_extension(DummyExtensionOne)
async def _require_extension_target_async(
    *, extension: DummyExtensionOne
) -> DummyExtensionOne:
    return extension


class _RequireExtensionTargetClassMethod:
    @classmethod
    @require_extension(DummyExtensionOne)
    async def target(cls, *, extension: DummyExtensionOne) -> DummyExtensionOne:
        return extension


class _RequireExtensionTargetInstanceMethod:
    @require_extension(DummyExtensionOne)
    async def target(self, *, extension: DummyExtensionOne) -> DummyExtensionOne:
        return extension


_test_require_extension_targets = pytest.mark.parametrize(
    "target",
    [
        _require_extension_target_sync,
        _require_extension_target_async,
        _RequireExtensionTargetClassMethod.target,
        _RequireExtensionTargetInstanceMethod().target,
    ],
)

_TestRequireExtensionTarget: TypeAlias = Callable[
    [Unpack[ServiceLevelKwargs]], Awaitable[DummyExtensionOne]
]


@_test_require_extension_targets
async def test_require_extension__with_universe(
    target: _TestRequireExtensionTarget,
) -> None:
    with (
        ExtensionDefinition.type().override_discovery(
            StaticDiscovery(DummyExtensionOne)
        ),
        pytest.raises(UnmetRequirement),
    ):
        await target(services=universe)


@_test_require_extension_targets
async def test_require_extension__with_app(
    isolated_app: App, target: _TestRequireExtensionTarget
) -> None:
    with (
        ExtensionDefinition.type().override_discovery(
            StaticDiscovery(DummyExtensionOne)
        ),
        pytest.raises(UnmetRequirement),
    ):
        await target(services=isolated_app)


@_test_require_extension_targets
async def test_require_extension__with_project(
    isolated_app: App, target: _TestRequireExtensionTarget
) -> None:
    with ExtensionDefinition.type().override_discovery(
        StaticDiscovery(DummyExtensionOne)
    ):
        async with Project.new_isolated(isolated_app) as project, project:
            with pytest.raises(UnmetRequirement):
                await target(services=project)


@_test_require_extension_targets
async def test_require_extension__with_extension(
    isolated_app: App, target: _TestRequireExtensionTarget
) -> None:
    with ExtensionDefinition.type().override_discovery(
        StaticDiscovery(DummyExtensionOne)
    ):
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.add(DummyExtensionOne)
            async with project:
                assert isinstance(await target(services=project), DummyExtensionOne)
