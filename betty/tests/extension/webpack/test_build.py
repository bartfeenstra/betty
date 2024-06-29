from asyncio import to_thread
from collections.abc import Sequence
from pathlib import Path
from shutil import rmtree

import pytest
from pytest_mock import MockerFixture

from betty._npm import NpmUnavailable
from betty.app import App
from betty.project import Project
from betty.project.extension import Extension
from betty.extension.webpack import WebpackEntryPointProvider
from betty.extension.webpack.build import Builder
from betty.job import Context
from betty.locale import DEFAULT_LOCALIZER


class DummyEntryPointProviderExtension(WebpackEntryPointProvider, Extension):
    @classmethod
    def webpack_entry_point_directory_path(cls) -> Path:
        return Path(__file__).parent / "test_build_webpack_entry_point"

    def webpack_entry_point_cache_keys(self) -> Sequence[str]:
        return ()


class TestBuilder:
    @pytest.mark.parametrize(
        (
            "with_entry_point_provider",
            "debug",
            "npm_install_cache_available",
            "webpack_build_cache_available",
        ),
        [
            (True, True, True, True),
            (False, True, True, True),
            (True, False, True, True),
            (True, True, True, False),
        ],
    )
    async def test_build(
        self,
        with_entry_point_provider: bool,
        debug: bool,
        new_temporary_app: App,
        npm_install_cache_available: bool,
        tmp_path: Path,
        webpack_build_cache_available: bool,
    ) -> None:
        project = Project(new_temporary_app)
        if with_entry_point_provider:
            project.configuration.extensions.enable(DummyEntryPointProviderExtension)
        job_context = Context()
        async with project:
            sut = Builder(
                tmp_path,
                (
                    [project.extensions[DummyEntryPointProviderExtension]]
                    if with_entry_point_provider
                    else []
                ),
                False,
                project.renderer,
                job_context=job_context,
                localizer=DEFAULT_LOCALIZER,
            )
            if npm_install_cache_available:
                webpack_build_directory_path = await sut.build()
                if not webpack_build_cache_available:
                    await to_thread(rmtree, webpack_build_directory_path)
            webpack_build_directory_path = await sut.build()
        assert (webpack_build_directory_path / "css" / "vendor.css").exists()
        assert (
            webpack_build_directory_path / "js" / "webpack-entry-loader.js"
        ).exists()
        if with_entry_point_provider:
            assert (
                webpack_build_directory_path
                / "js"
                / f"{DummyEntryPointProviderExtension.name()}.js"
            ).exists()

    async def test_build_with_npm_unavailable(
        self, mocker: MockerFixture, tmp_path: Path
    ) -> None:
        m_npm = mocker.patch("betty._npm.npm")
        m_npm.side_effect = NpmUnavailable()

        job_context = Context()
        m_renderer = mocker.AsyncMock()
        sut = Builder(
            tmp_path,
            [],
            False,
            m_renderer,
            job_context=job_context,
            localizer=DEFAULT_LOCALIZER,
        )
        with pytest.raises(NpmUnavailable):
            await sut.build()
