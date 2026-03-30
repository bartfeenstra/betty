from pathlib import Path

import aiofiles
from pytest_mock import MockerFixture

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
        webpack_build_directory_path = tmp_path
        m_build = mocker.patch("betty.plugins.extension.webpack.build.Builder.build")
        m_build.return_value = webpack_build_directory_path

        async with aiofiles.open(
            webpack_build_directory_path / self._SENTINEL, "w"
        ) as f:
            await f.write(self._SENTINEL)

        async with isolated_project_factory(service_plugins=[Webpack]) as project:
            await generate(project)

            async with aiofiles.open(project.www_directory / self._SENTINEL) as f:
                assert await f.read() == self._SENTINEL
