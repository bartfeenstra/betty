from collections.abc import Awaitable, Callable
from typing import TypeAlias, Unpack

import pytest

from betty.app import App
from betty.exception import HumanFacingException
from betty.project import Project
from betty.service.level.universal import universe
from betty.service.requirement import ServiceLevelKwargs
from betty.service.requirement.project import require_project


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
    with pytest.raises(HumanFacingException):
        await target(services=universe)


@_test_require_project_targets
async def test_require_project__with_app(
    isolated_app: App, target: _TestRequireProjectTarget
) -> None:
    with pytest.raises(HumanFacingException):
        await target(services=isolated_app)


@_test_require_project_targets
async def test_require_project__with_project(
    isolated_app: App, target: _TestRequireProjectTarget
) -> None:
    async with Project.new_isolated(isolated_app) as project, project:
        assert await target(services=project) is project
