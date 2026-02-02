from collections.abc import Awaitable, Callable
from typing import TypeAlias, Unpack

import pytest

from betty.app import App
from betty.exception import HumanFacingException
from betty.project import Project
from betty.service.level import universe
from betty.service.requirement import ServiceLevelKwargs
from betty.service.requirement.app import require_app


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
    with pytest.raises(HumanFacingException):
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
