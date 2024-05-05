from pathlib import Path

import aiofiles
import pytest
from aiofiles.os import makedirs
from pytest_mock import MockerFixture

from betty import fs
from betty._npm import NpmUnavailable
from betty.app import App
from betty.extension.webpack import PrebuiltAssetsRequirement, Webpack
from betty.extension.webpack.build import webpack_build_id
from betty.generate import generate
from betty.job import Context
from betty.requirement import RequirementError


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


class TestWebpack:
    _SENTINEL = "s3nt1n3l"

    async def test_generate_with_npm(
        self, mocker: MockerFixture, tmp_path: Path
    ) -> None:
        webpack_build_directory_path = tmp_path
        m_build = mocker.patch("betty.extension.webpack.build.Builder.build")
        m_build.return_value = webpack_build_directory_path

        async with aiofiles.open(
            webpack_build_directory_path / self._SENTINEL, "w"
        ) as f:
            await f.write(self._SENTINEL)

        async with App.new_temporary() as app:
            app.project.configuration.extensions.enable(Webpack)
            await generate(app)

        async with aiofiles.open(
            app.project.configuration.www_directory_path / self._SENTINEL
        ) as f:
            assert await f.read() == self._SENTINEL

    async def test_generate_without_npm_with_prebuild(
        self, mocker: MockerFixture, tmp_path: Path
    ) -> None:
        m_build = mocker.patch("betty.extension.webpack.build.Builder.build")
        m_build.side_effect = NpmUnavailable()

        webpack_build_directory_path = (
            tmp_path / "webpack" / f"build-{webpack_build_id(())}"
        )
        await makedirs(webpack_build_directory_path)
        async with aiofiles.open(
            webpack_build_directory_path / self._SENTINEL, "w"
        ) as f:
            await f.write(self._SENTINEL)

        original_prebuilt_assets_directory_path = fs.PREBUILT_ASSETS_DIRECTORY_PATH
        fs.PREBUILT_ASSETS_DIRECTORY_PATH = tmp_path
        try:
            async with App.new_temporary() as app:
                app.project.configuration.extensions.enable(Webpack)
                await generate(app)
        finally:
            fs.PREBUILT_ASSETS_DIRECTORY_PATH = original_prebuilt_assets_directory_path

        async with aiofiles.open(
            app.project.configuration.www_directory_path / self._SENTINEL
        ) as f:
            assert await f.read() == self._SENTINEL

    async def test_generate_without_npm_without_prebuild(
        self, mocker: MockerFixture, tmp_path: Path
    ) -> None:
        prebuilt_assets_directory_path = tmp_path

        m_build = mocker.patch("betty.extension.webpack.build.Builder.build")
        m_build.side_effect = NpmUnavailable()

        original_prebuilt_assets_directory_path = fs.PREBUILT_ASSETS_DIRECTORY_PATH
        fs.PREBUILT_ASSETS_DIRECTORY_PATH = (
            Path(prebuilt_assets_directory_path) / "does-not-exist"
        )
        try:
            async with App.new_temporary() as app:
                app.project.configuration.extensions.enable(Webpack)
                with pytest.raises(ExceptionGroup) as exc_info:
                    await generate(app)
                error = exc_info.value
                assert isinstance(error, ExceptionGroup)
                assert error.subgroup(RequirementError) is not None
        finally:
            fs.PREBUILT_ASSETS_DIRECTORY_PATH = original_prebuilt_assets_directory_path

    async def test_prebuild(self, mocker: MockerFixture, tmp_path: Path) -> None:
        webpack_build_directory_path = (
            tmp_path / "webpack" / f"build-{webpack_build_id(())}"
        )
        prebuilt_assets_directory_path = tmp_path / "prebuild"

        m_build = mocker.patch("betty.extension.webpack.build.Builder.build")
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
            async with App.new_temporary() as app:
                app.project.configuration.extensions.enable(Webpack)
                webpack = app.extensions[Webpack]
                await webpack.prebuild(job_context)
        finally:
            fs.PREBUILT_ASSETS_DIRECTORY_PATH = original_prebuilt_assets_directory_path

        async with aiofiles.open(
            prebuilt_assets_directory_path
            / "webpack"
            / f"build-{webpack_build_id(())}"
            / self._SENTINEL
        ) as f:
            assert await f.read() == self._SENTINEL
