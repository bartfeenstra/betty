import pytest

from betty.app import App
from betty.exception import HumanFacingException
from betty.project import Project
from betty.service.level import UNIVERSE
from betty.service.requirement.project import require_project


@require_project
def _require_project_target(project: Project, /) -> Project:
    return project


async def test_require_project__with_universe() -> None:
    with pytest.raises(HumanFacingException):
        await _require_project_target(UNIVERSE)


async def test_require_project__with_app(isolated_app: App) -> None:
    with pytest.raises(HumanFacingException):
        await _require_project_target(isolated_app)


async def test_require_project__with_project(isolated_app: App) -> None:
    async with Project.new_isolated(isolated_app) as project, project:
        assert await _require_project_target(project) is project
