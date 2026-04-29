from pathlib import Path

from pytest_mock import MockerFixture

from betty.file import read, write
from betty.plugins.extension.webpack import Webpack
from betty.project.generate import generate
from betty.test_utils.conftest import IsolatedProjectFactory


class TestWebpack:
    _SENTINEL = "s3nt1n3l"

    async def test_generate__with_npm(
        self,
        mocker: MockerFixture,
        isolated_project_factory: IsolatedProjectFactory,
        tmp_path: Path,
    ) -> None:
        webpack_build_directory = tmp_path
        m_build = mocker.patch("betty.plugins.extension.webpack.build.Builder.build")
        m_build.return_value = webpack_build_directory

        await write(webpack_build_directory / self._SENTINEL, self._SENTINEL)
        async with isolated_project_factory(extensions=[Webpack]) as project:
            await generate(project)
            assert await read(project.www_directory / self._SENTINEL) == self._SENTINEL
