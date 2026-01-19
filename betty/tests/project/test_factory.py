from typing import Self

import pytest
from typing_extensions import override

from betty.app import App
from betty.factory import FactoryError
from betty.project import Project
from betty.project.factory import require_project
from betty.service.level.factory import (
    CallbackServiceLevelDependentFactory,
    ServiceLevelDependentFactory,
    ServiceLevelDependentSelfFactory,
    ServiceLevelTarget,
)
from betty.service.level.universal import universe


class _Target:
    def __init__(self, project: Project):
        self.project = project


@require_project
def _require_project_target_sync(project: Project) -> _Target:
    return _Target(project)


@require_project
async def _require_project_target_async(project: Project) -> _Target:
    return _Target(project)


class _RequireAppSelfTarget(_Target, ServiceLevelDependentSelfFactory):
    @override
    @classmethod
    @require_project
    async def new_for_services(cls, project: Project, /) -> Self:
        return cls(project)


class _RequireAppTarget(ServiceLevelDependentFactory[_Target]):
    @override
    @require_project
    async def new_for_services(self, project: Project, /) -> _Target:
        return _Target(project)


_targets = pytest.mark.parametrize(
    "target",
    [
        CallbackServiceLevelDependentFactory(_require_project_target_sync),
        CallbackServiceLevelDependentFactory(_require_project_target_async),
        _RequireAppTarget(),
        _RequireAppSelfTarget,
    ],
)


@_targets
async def test_require_project__without_app(
    target: ServiceLevelTarget[_Target],
) -> None:
    with pytest.raises(FactoryError):
        await universe.new_target(target)


@_targets
async def test_require_project__with_app(
    isolated_app: App, target: ServiceLevelTarget[_Target]
) -> None:
    with pytest.raises(FactoryError):
        await isolated_app.new_target(target)


@_targets
async def test_require_project__with_project(
    isolated_app: App, target: ServiceLevelTarget[_Target]
) -> None:
    async with Project.new_isolated(isolated_app) as project, project:
        assert (await project.new_target(target)).project is project
