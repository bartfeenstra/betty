from collections.abc import Sequence
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from betty._npm import NpmUnavailable
from betty.app import App
from betty.job import Context
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.plugin.static import StaticPluginRepository
from betty.project import Project
from betty.project.extension.webpack import WebpackEntryPointProvider
from betty.project.extension.webpack.build import Builder
from betty.test_utils.project.extension import DummyExtension


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

    async def test_build(self, new_temporary_app: App, tmp_path: Path) -> None:
        # Loop instead of parameterization, so we can reuse caches.
        for with_entry_point_provider, debug in [
            # With an entry point provider and debug.
            (True, True),
            # Without an entry point provider or debug.
            (False, False),
        ]:
            async with Project.new_temporary(new_temporary_app) as project:
                project.configuration.debug = debug
                if with_entry_point_provider:
                    project.configuration.extensions.enable(
                        DummyEntryPointProviderExtension
                    )
                job_context = Context()
                async with project:
                    extensions = await project.extensions
                    sut = Builder(
                        tmp_path,
                        (
                            [extensions[DummyEntryPointProviderExtension]]
                            if with_entry_point_provider
                            else []
                        ),
                        False,
                        await project.renderer,
                        job_context=job_context,
                        localizer=DEFAULT_LOCALIZER,
                    )
                    # Build twice, to test with warm caches as well.
                    await sut.build()
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
