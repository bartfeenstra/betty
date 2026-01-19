from typing import Self

import pytest
from typing_extensions import override

from betty.app import App
from betty.app.factory import require_app
from betty.factory import FactoryError
from betty.project import Project
from betty.service.level.factory import (
    CallbackServiceLevelDependentFactory,
    ServiceLevelDependentFactory,
    ServiceLevelDependentSelfFactory,
    ServiceLevelTarget,
)
from betty.service.level.universal import universe


class _Target:
    def __init__(self, app: App):
        self.app = app


@require_app
def _require_app_target_sync(app: App) -> _Target:
    return _Target(app)


@require_app
async def _require_app_target_async(app: App) -> _Target:
    return _Target(app)


class _RequireAppSelfTarget(_Target, ServiceLevelDependentSelfFactory):
    @override
    @classmethod
    @require_app
    async def new_for_services(cls, app: App, /) -> Self:
        return cls(app)


class _RequireAppTarget(ServiceLevelDependentFactory[_Target]):
    @override
    @require_app
    async def new_for_services(self, app: App, /) -> _Target:
        return _Target(app)


_targets = pytest.mark.parametrize(
    "target",
    [
        CallbackServiceLevelDependentFactory(_require_app_target_sync),
        CallbackServiceLevelDependentFactory(_require_app_target_async),
        _RequireAppTarget(),
        _RequireAppSelfTarget,
    ],
)


@_targets
async def test_require_app__without_app(target: ServiceLevelTarget[_Target]) -> None:
    with pytest.raises(FactoryError):
        await universe.new_target(target)


@_targets
async def test_require_app__with_app(
    isolated_app: App, target: ServiceLevelTarget[_Target]
) -> None:
    assert (await isolated_app.new_target(target)).app is isolated_app


@_targets
async def test_require_app__with_project(
    isolated_app: App, target: ServiceLevelTarget[_Target]
) -> None:
    async with Project.new_isolated(isolated_app) as project, project:
        assert (await project.new_target(target)).app is isolated_app
