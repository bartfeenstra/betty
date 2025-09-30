from collections.abc import AsyncIterator
from pathlib import Path

import aiofiles
import pytest
from pytest_mock import MockerFixture
from typing_extensions import override

from betty._npm import NpmUnavailable
from betty.app import App
from betty.job.scheduler import Cancelled
from betty.project import Project
from betty.project.config import ProjectConfiguration
from betty.project.extension import Extension
from betty.project.extension.webpack import Webpack
from betty.project.generate import generate
from betty.requirement import RequirementError
from betty.test_utils.project.extension import ExtensionTestBase


class TestWebpack(ExtensionTestBase):
    _SENTINEL = "s3nt1n3l"

    @override
    @pytest.fixture
    async def sut(self, new_temporary_app: App) -> AsyncIterator[Extension]:
        async with (
            Project.new_temporary(new_temporary_app) as project,
            project,
            await Webpack.new_for_project(project) as sut,
        ):
            yield sut

    async def test_get_public_js_paths(self, sut: Webpack) -> None:
        assert await sut.get_public_js_paths()

    async def test_filters(self, sut: Webpack) -> None:
        assert sut.filters

    async def test_get_public_css_paths(self, sut: Webpack) -> None:
        assert await sut.get_public_css_paths()

    async def test_generate__with_npm(
        self, mocker: MockerFixture, new_temporary_app: App, tmp_path: Path
    ) -> None:
        webpack_build_directory_path = tmp_path
        m_build = mocker.patch("betty.project.extension.webpack.build.Builder.build")
        m_build.return_value = webpack_build_directory_path

        async with aiofiles.open(
            webpack_build_directory_path / self._SENTINEL, "w"
        ) as f:
            await f.write(self._SENTINEL)

        async with Project.new_temporary(new_temporary_app) as project:
            project.configuration.extensions.enable(Webpack)
            async with project:
                await generate(project)

                async with aiofiles.open(
                    project.configuration.www_directory_path / self._SENTINEL
                ) as f:
                    assert await f.read() == self._SENTINEL

    async def test_generate__without_npm(
        self, mocker: MockerFixture, new_temporary_app: App, tmp_path: Path
    ) -> None:
        m_build = mocker.patch("betty.project.extension.webpack.build.Builder.build")
        m_build.side_effect = NpmUnavailable()

        project = await Project.new(
            new_temporary_app,
            configuration=await ProjectConfiguration.new(
                tmp_path / "project" / "betty.json"
            ),
        )
        project.configuration.extensions.enable(Webpack)
        async with project:
            with pytest.raises(Cancelled) as exc_info:
                await generate(project)
            assert isinstance(exc_info.value.__cause__, RequirementError)
