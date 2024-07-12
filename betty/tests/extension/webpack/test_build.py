from asyncio import to_thread
from collections.abc import Sequence
from pathlib import Path
from shutil import rmtree

import pytest
from pytest_mock import MockerFixture

from betty._npm import NpmUnavailable
from betty.app import App
from betty.extension.webpack import WebpackEntryPointProvider
from betty.extension.webpack.build import Builder
from betty.job import Context
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.plugin.static import StaticPluginRepository
from betty.project import Project
from betty.tests.project.extension.test___init__ import DummyExtension


class DummyEntryPointProviderExtension(WebpackEntryPointProvider, DummyExtension):
    @classmethod
    def webpack_entry_point_directory_path(cls) -> Path:
        return Path(__file__).parent / "test_build_webpack_entry_point"

    def webpack_entry_point_cache_keys(self) -> Sequence[str]:
        return ()


class TestBuilder:
    @pytest.fixture(autouse=True)
    def _extensions(self, mocker: MockerFixture) -> None:
        mocker.patch(
            "betty.project.extension.EXTENSION_REPOSITORY",
            new=StaticPluginRepository(DummyEntryPointProviderExtension),
        )

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
        async with Project.new_temporary(new_temporary_app) as project:
            if with_entry_point_provider:
                project.configuration.extensions.enable(
                    DummyEntryPointProviderExtension
                )
            job_context = Context()
            async with project:
                sut = Builder(
                    tmp_path,
                    (
                        [
                            project.extensions[  # type: ignore[list-item]
                                DummyEntryPointProviderExtension.plugin_id()
                            ]
                        ]
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
                    / f"{DummyEntryPointProviderExtension.plugin_id()}.js"
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
