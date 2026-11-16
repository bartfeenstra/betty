from pathlib import Path

from pytest_mock import MockerFixture

from betty.file import read, write
from betty.project import Project
from betty.project.generate import generate
from betty.service_providers.webpack import Webpack
from betty.test_utils.conftest import NewIsolatedProject


class TestWebpack:
    _SENTINEL = "s3nt1n3l"

    async def test_generate__with_npm(
        self,
        mocker: MockerFixture,
        new_isolated_project: NewIsolatedProject,
        tmp_path: Path,
    ) -> None:
        webpack_build_directory = tmp_path
        m_build = mocker.patch("betty.service_providers.webpack.build.Builder.build")
        m_build.return_value = webpack_build_directory

        await write(webpack_build_directory / self._SENTINEL, self._SENTINEL)
        async with new_isolated_project() as project:
            Project.service_providers.add_init_plugins(project, Webpack)
            async with project:
                await generate(project)
                assert (
                    await read(project.www_directory / self._SENTINEL) == self._SENTINEL
                )

    async def test_builder(self, new_isolated_project: NewIsolatedProject) -> None:
        async with new_isolated_project() as project:
            Project.service_providers.add_init_plugins(project, Webpack)
            async with project:
                webpack = await project.service_providers[Webpack]
                assert await webpack.builder is await webpack.builder
