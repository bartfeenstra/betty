from asyncio import to_thread
from collections.abc import Sequence
from pathlib import Path
from shutil import rmtree

import pytest
from pytest_mock import MockerFixture

from betty._npm import NpmUnavailable
from betty.app import App
from betty.app.extension import Extension
from betty.extension.webpack import WebpackEntrypointProvider
from betty.extension.webpack.build import Builder
from betty.job import Context
from betty.locale import DEFAULT_LOCALIZER


class DummyEntrypointProviderExtension(WebpackEntrypointProvider, Extension):
    @classmethod
    def webpack_entrypoint_directory_path(cls) -> Path:
        return Path(__file__).parent / "test_build_webpack_entrypoint"

    def webpack_entrypoint_cache_keys(self) -> Sequence[str]:
        return ()


class TestBuilder:
    async def test_build(self, tmp_path: Path) -> None:
        await self._test_build(tmp_path, True, True, True, True)

    async def test_build_without_entrypoint_provider(self, tmp_path: Path) -> None:
        await self._test_build(tmp_path, False, True, True, True)

    async def test_build_without_debug(self, tmp_path: Path) -> None:
        await self._test_build(tmp_path, True, False, True, True)

    async def test_build_without_npm_install_cache_available(
        self, tmp_path: Path
    ) -> None:
        await self._test_build(tmp_path, True, True, False, True)

    async def _test_build(
        self,
        tmp_path: Path,
        with_entrypoint_provider: bool,
        debug: bool,
        npm_install_cache_available: bool,
        webpack_build_cache_available: bool,
    ) -> None:
        async with App.new_temporary() as app:
            if with_entrypoint_provider:
                app.project.configuration.extensions.enable(
                    DummyEntrypointProviderExtension
                )
            job_context = Context()
            sut = Builder(
                tmp_path,
                (
                    [app.extensions[DummyEntrypointProviderExtension]]
                    if with_entrypoint_provider
                    else []
                ),
                debug,
                app.renderer,
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
        if with_entrypoint_provider:
            assert (
                webpack_build_directory_path
                / "js"
                / f"{DummyEntrypointProviderExtension.name()}.js"
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
