from collections.abc import Awaitable, Callable
from typing import TypeAlias, Unpack

import pytest

from betty.app import App
from betty.exception import HumanFacingException
from betty.extension import ExtensionDefinition
from betty.project import Project
from betty.service.level import universe
from betty.service.requirement import ServiceLevelKwargs
from betty.service.requirement.extension import require_extension
from betty.test_utils.project.extension import DummyExtensionOne


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
        ExtensionDefinition.type().discoverer.override(DummyExtensionOne),
        pytest.raises(HumanFacingException),
    ):
        await target(services=universe)


@_test_require_extension_targets
async def test_require_extension__with_app(
    isolated_app: App, target: _TestRequireExtensionTarget
) -> None:
    with (
        ExtensionDefinition.type().discoverer.override(DummyExtensionOne),
        pytest.raises(HumanFacingException),
    ):
        await target(services=isolated_app)


@_test_require_extension_targets
async def test_require_extension__with_project(
    isolated_app: App, target: _TestRequireExtensionTarget
) -> None:
    with ExtensionDefinition.type().discoverer.override(DummyExtensionOne):
        async with Project.new_isolated(isolated_app) as project, project:
            with pytest.raises(HumanFacingException):
                await target(services=project)


@_test_require_extension_targets
async def test_require_extension__with_extension(
    isolated_app: App, target: _TestRequireExtensionTarget
) -> None:
    with ExtensionDefinition.type().discoverer.override(DummyExtensionOne):
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.add(DummyExtensionOne)
            async with project:
                assert isinstance(await target(services=project), DummyExtensionOne)
