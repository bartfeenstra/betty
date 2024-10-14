from pathlib import Path

import aiofiles
import pytest
from aiofiles.os import makedirs
from pytest_mock import MockerFixture
from typing_extensions import override

from betty import fs
from betty._npm import NpmUnavailable
from betty.app import App
from betty.job import Context
from betty.project import Project
from betty.project.config import ProjectConfiguration
from betty.project.extension.webpack import PrebuiltAssetsRequirement, Webpack
from betty.project.extension.webpack.build import webpack_build_id
from betty.project.generate import generate
from betty.requirement import RequirementError
from betty.test_utils.project.extension import ExtensionTestBase


class TestPrebuiltAssetsRequirement:
    @pytest.mark.parametrize(
        "expected",
        [
            True,
            False,
        ],
    )
    async def test_is_met(self, expected: bool, tmp_path: Path) -> None:
        prebuilt_assets_directory_path = tmp_path
        if expected:
            (prebuilt_assets_directory_path / "webpack").mkdir()
        original_prebuilt_assets_directory_path = fs.PREBUILT_ASSETS_DIRECTORY_PATH
        fs.PREBUILT_ASSETS_DIRECTORY_PATH = Path(prebuilt_assets_directory_path)
        sut = PrebuiltAssetsRequirement()
        try:
            assert sut.is_met() is expected
        finally:
            fs.PREBUILT_ASSETS_DIRECTORY_PATH = original_prebuilt_assets_directory_path


class TestWebpack(ExtensionTestBase[Webpack]):
    _SENTINEL = "s3nt1n3l"

    @override
    def get_sut_class(self) -> type[Webpack]:
        return Webpack

    async def test_filters(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            sut = await project.new_target(self.get_sut_class())
            assert len(sut.filters)

    async def test_public_css_paths(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            sut = await project.new_target(self.get_sut_class())
            assert len(sut.public_css_paths)

    async def test_generate_with_npm(
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

    async def test_generate_without_npm_with_prebuild(
        self, mocker: MockerFixture, new_temporary_app: App, tmp_path: Path
    ) -> None:
        m_build = mocker.patch("betty.project.extension.webpack.build.Builder.build")
        m_build.side_effect = NpmUnavailable()

        webpack_build_directory_path = (
            tmp_path / "webpack" / f"build-{webpack_build_id((), False)}"
        )
        await makedirs(webpack_build_directory_path)
        async with aiofiles.open(
            webpack_build_directory_path / self._SENTINEL, "w"
        ) as f:
            await f.write(self._SENTINEL)

        original_prebuilt_assets_directory_path = fs.PREBUILT_ASSETS_DIRECTORY_PATH
        fs.PREBUILT_ASSETS_DIRECTORY_PATH = tmp_path
        try:
            async with Project.new_temporary(new_temporary_app) as project:
                project.configuration.extensions.enable(Webpack)
                async with project:
                    await generate(project)
                    async with aiofiles.open(
                        project.configuration.www_directory_path / self._SENTINEL
                    ) as f:
                        assert await f.read() == self._SENTINEL
        finally:
            fs.PREBUILT_ASSETS_DIRECTORY_PATH = original_prebuilt_assets_directory_path

    async def test_generate_without_npm_without_prebuild(
        self, mocker: MockerFixture, new_temporary_app: App, tmp_path: Path
    ) -> None:
        prebuilt_assets_directory_path = tmp_path

        m_build = mocker.patch("betty.project.extension.webpack.build.Builder.build")
        m_build.side_effect = NpmUnavailable()

        original_prebuilt_assets_directory_path = fs.PREBUILT_ASSETS_DIRECTORY_PATH
        fs.PREBUILT_ASSETS_DIRECTORY_PATH = (
            Path(prebuilt_assets_directory_path) / "does-not-exist"
        )
        try:
            project = await Project.new(
                new_temporary_app,
                configuration=await ProjectConfiguration.new(
                    tmp_path / "project" / "betty.json"
                ),
            )
            project.configuration.extensions.enable(Webpack)
            async with project:
                with pytest.raises(RequirementError):
                    await generate(project)
        finally:
            fs.PREBUILT_ASSETS_DIRECTORY_PATH = original_prebuilt_assets_directory_path

    async def test_prebuild(
        self, mocker: MockerFixture, new_temporary_app: App, tmp_path: Path
    ) -> None:
        webpack_build_directory_path = (
            tmp_path / "webpack" / f"build-{webpack_build_id((),False)}"
        )
        prebuilt_assets_directory_path = tmp_path / "prebuild"

        m_build = mocker.patch("betty.project.extension.webpack.build.Builder.build")
        m_build.return_value = webpack_build_directory_path

        await makedirs(webpack_build_directory_path)
        async with aiofiles.open(
            webpack_build_directory_path / self._SENTINEL, "w"
        ) as f:
            await f.write(self._SENTINEL)

        original_prebuilt_assets_directory_path = fs.PREBUILT_ASSETS_DIRECTORY_PATH
        fs.PREBUILT_ASSETS_DIRECTORY_PATH = prebuilt_assets_directory_path
        try:
            job_context = Context()
            async with Project.new_temporary(new_temporary_app) as project:
                project.configuration.extensions.enable(Webpack)
                async with project:
                    extensions = await project.extensions
                    webpack = extensions[Webpack]
                    await webpack.prebuild(job_context)
                    async with aiofiles.open(
                        prebuilt_assets_directory_path
                        / "webpack"
                        / f"build-{webpack_build_id((),False)}"
                        / self._SENTINEL
                    ) as f:
                        assert await f.read() == self._SENTINEL
        finally:
            fs.PREBUILT_ASSETS_DIRECTORY_PATH = original_prebuilt_assets_directory_path
