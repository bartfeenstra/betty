from pathlib import Path

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

        with open(
            webpack_build_directory_path / self._SENTINEL, "w", encoding="utf-8"
        ) as f:
            f.write(self._SENTINEL)

        async with isolated_project_factory(extensions=[Webpack]) as project:
            await generate(project)

            with open(project.www_directory / self._SENTINEL, encoding="utf-8") as f:
                assert f.read() == self._SENTINEL
