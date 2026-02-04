import pytest

from betty.app import App
from betty.exception import HumanFacingException
from betty.project import Project
from betty.service.level import universe
from betty.service.requirement.app import require_app


@require_app
def _require_app_target(app: App, /) -> App:
    return app


async def test_require_app__with_universe() -> None:
    with pytest.raises(HumanFacingException):
        await _require_app_target(universe)


async def test_require_app__with_app(isolated_app: App) -> None:
    assert await _require_app_target(isolated_app) is isolated_app


async def test_require_app__with_project(isolated_app: App) -> None:
    async with Project.new_isolated(isolated_app) as project, project:
        assert await _require_app_target(project) is isolated_app
