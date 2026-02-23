from betty.app import App
from betty.extension.spdx import Spdx
from betty.project import Project


class TestSpdx:
    async def test_licenses(self, isolated_app: App) -> None:
        async with (
            Project.new_isolated(isolated_app) as project,
            project,
            await Spdx.new(project) as sut,
        ):
            await sut.licenses
