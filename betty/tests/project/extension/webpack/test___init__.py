from pathlib import Path

import pytest
from pytest_mock import MockerFixture
from typing_extensions import override

from betty import fs
from betty._npm import NpmUnavailable
from betty.app import App
from betty.project import Project
from betty.project.extension.webpack import PrebuiltAssetsRequirement, Webpack
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

    @pytest.mark.parametrize(
        "watch",
        [
            True,
            False,
        ],
    )
    async def test_generate(
        self, mocker: MockerFixture, new_temporary_app: App, tmp_path: Path, watch: bool
    ) -> None:
        m_build = mocker.patch("betty.project.extension.webpack.build.Builder.build")

        async with Project.new_temporary(new_temporary_app) as project:
            project.configuration.extensions.enable(Webpack)
            async with project:
                await generate(project, watch=watch)

        m_build.assert_called_once_with(watch=watch)

    @pytest.mark.parametrize(
        "watch",
        [
            True,
            False,
        ],
    )
    async def test_generate_with_npm_unavailable(
        self, mocker: MockerFixture, new_temporary_app: App, tmp_path: Path, watch: bool
    ) -> None:
        m_build = mocker.patch(
            "betty.project.extension.webpack.build.Builder.build",
            side_effect=NpmUnavailable,
        )

        async with Project.new_temporary(new_temporary_app) as project:
            project.configuration.extensions.enable(Webpack)
            async with project:
                with pytest.raises(RequirementError):
                    await generate(project, watch=watch)

        m_build.assert_called_once_with(watch=watch)
