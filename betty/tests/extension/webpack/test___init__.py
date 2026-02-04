from pathlib import Path

import aiofiles
from pytest_mock import MockerFixture

from betty.app import App
from betty.extension.webpack import Webpack
from betty.project import Project
from betty.project.generate import generate


class TestWebpack:
    _SENTINEL = "s3nt1n3l"

    async def test_get_public_js_paths(self, isolated_app: App) -> None:
        async with (
            Project.new_isolated(isolated_app) as project,
            project,
            await Webpack.new(project) as sut,
        ):
            assert await sut.get_public_js_paths()

    async def test_filters(self, isolated_app: App) -> None:
        async with (
            Project.new_isolated(isolated_app) as project,
            project,
            await Webpack.new(project) as sut,
        ):
            assert sut.filters

    async def test_get_public_css_paths(self, isolated_app: App) -> None:
        async with (
            Project.new_isolated(isolated_app) as project,
            project,
            await Webpack.new(project) as sut,
        ):
            assert await sut.get_public_css_paths()

    async def test_generate__with_npm(
        self, mocker: MockerFixture, isolated_app: App, tmp_path: Path
    ) -> None:
        webpack_build_directory_path = tmp_path
        m_build = mocker.patch("betty.extension.webpack.build.Builder.build")
        m_build.return_value = webpack_build_directory_path

        async with aiofiles.open(
            webpack_build_directory_path / self._SENTINEL, "w"
        ) as f:
            await f.write(self._SENTINEL)

        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.add(Webpack)
            async with project:
                await generate(project)

                async with aiofiles.open(project.www_directory / self._SENTINEL) as f:
                    assert await f.read() == self._SENTINEL

    async def test_new_document_vars(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            sut = await Webpack.new(project)
            assert sut.new_document_vars()
