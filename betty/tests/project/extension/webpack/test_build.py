from collections.abc import Sequence
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from betty import fs
from betty._npm import NpmUnavailable
from betty.app import App
from betty.project import Project
from betty.project.extension.webpack.build import Builder, EntryPointProvider, prebuild
from betty.test_utils.project.extension import DummyExtension


class DummyEntryPointProviderExtension(EntryPointProvider, DummyExtension):
    @classmethod
    def webpack_entry_point_directory_path(cls) -> Path:
        return Path(__file__).parent / "test_build_webpack_entry_point"

    async def webpack_entry_point_cache_keys(self) -> Sequence[str]:
        return ()


class TestBuilder:
    async def test_build(self, new_temporary_app: App, tmp_path: Path) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            sut = Builder(project)
            await sut.build()
            assert (
                project.configuration.www_directory_path
                / "js"
                / "webpack-entry-loader.js"
            ).exists()

    async def test_build_without_npm_without_prebuild(
        self, mocker: MockerFixture, new_temporary_app: App, tmp_path: Path
    ) -> None:
        fs_prebuilt_assets_directory_path = tmp_path / "prebuild"
        original_fs_prebuilt_assets_directory_path = fs.PREBUILT_ASSETS_DIRECTORY_PATH
        fs.PREBUILT_ASSETS_DIRECTORY_PATH = fs_prebuilt_assets_directory_path
        try:
            mocker.patch("betty._npm.npm", side_effect=NpmUnavailable)

            async with Project.new_temporary(new_temporary_app) as project, project:
                sut = Builder(project)
                with pytest.raises(NpmUnavailable):
                    await sut.build()
        finally:
            fs.PREBUILT_ASSETS_DIRECTORY_PATH = (
                original_fs_prebuilt_assets_directory_path
            )

    async def test_build_without_npm_with_prebuild(
        self, mocker: MockerFixture, new_temporary_app: App, tmp_path: Path
    ) -> None:
        fs_prebuilt_assets_directory_path = tmp_path / "prebuild"
        original_fs_prebuilt_assets_directory_path = fs.PREBUILT_ASSETS_DIRECTORY_PATH
        fs.PREBUILT_ASSETS_DIRECTORY_PATH = fs_prebuilt_assets_directory_path
        try:
            mocker.patch("betty._npm.npm", side_effect=NpmUnavailable)

            runtime_js_path = (
                fs_prebuilt_assets_directory_path
                / "webpack"
                / "build-a85c5c993ef281257f732d21cfa79095"
                / "www"
                / "js"
                / "webpack-entry-loader.js"
            )
            runtime_js_path.parent.mkdir(parents=True)
            runtime_js_path.touch()

            async with Project.new_temporary(new_temporary_app) as project, project:
                sut = Builder(project)
                await sut.build()
                assert (
                    project.configuration.www_directory_path
                    / "js"
                    / "webpack-entry-loader.js"
                ).exists()
        finally:
            fs.PREBUILT_ASSETS_DIRECTORY_PATH = (
                original_fs_prebuilt_assets_directory_path
            )

    async def test_prebuild(self, tmp_path: Path) -> None:
        fs_prebuilt_assets_directory_path = tmp_path / "prebuild"
        original_fs_prebuilt_assets_directory_path = fs.PREBUILT_ASSETS_DIRECTORY_PATH
        fs.PREBUILT_ASSETS_DIRECTORY_PATH = fs_prebuilt_assets_directory_path
        try:
            prebuilt_assets_directory_path = await prebuild()
            assert (
                fs_prebuilt_assets_directory_path
                in prebuilt_assets_directory_path.parents
            )
            assert (
                prebuilt_assets_directory_path
                / "www"
                / "js"
                / "webpack-entry-loader.js"
            ).exists()
        finally:
            fs.PREBUILT_ASSETS_DIRECTORY_PATH = (
                original_fs_prebuilt_assets_directory_path
            )
