from collections.abc import Sequence
from pathlib import Path

import aiofiles
import pytest
from pytest_mock import MockerFixture
from typing_extensions import override

from betty._npm import NpmUnavailable
from betty.app import App
from betty.job import Context
from betty.locale.localizable import Plain
from betty.plugin.static import StaticPluginRepository
from betty.project import Project
from betty.project.extension import Extension, ExtensionDefinition
from betty.project.extension.webpack.build import Builder, EntryPointProvider
from betty.test_utils.user import StaticUser


@ExtensionDefinition(
    id="dummy",
    label=Plain(""),
)
class DummyEntryPointProviderExtension(EntryPointProvider, Extension):
    @override
    @classmethod
    def webpack_entry_point_directory_path(cls) -> Path:
        return Path(__file__).parent / "test_build_webpack_entry_point"

    @override
    def webpack_entry_point_cache_keys(self) -> Sequence[str]:
        return ()


class TestBuilder:
    @pytest.fixture(autouse=True)
    def _extensions(self, mocker: MockerFixture) -> None:
        mocker.patch(
            "betty.project.extension.EXTENSION_REPOSITORY",
            new=StaticPluginRepository(ExtensionDefinition),
        )

    async def test_build(self, new_temporary_app: App, tmp_path: Path) -> None:
        # Loop instead of parameterization, so we can reuse caches.
        for index, (with_entry_point_provider, debug, root_path) in enumerate(
            [
                # With an entry point provider and debug.
                (True, True, ""),
                # With an entry point provider and a root path.
                (True, False, "/root-path"),
                # Without an entry point provider or debug.
                (False, False, ""),
            ]
        ):
            await self._test_build(
                new_temporary_app,
                tmp_path / str(index),
                with_entry_point_provider,
                debug,
                root_path,
            )

    async def _test_build(
        self,
        new_temporary_app: App,
        tmp_path: Path,
        with_entry_point_provider: bool,
        debug: bool,
        root_path: str,
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as project:
            job_context = Context()
            async with project:
                sut = Builder(
                    tmp_path,
                    (
                        [
                            await DummyEntryPointProviderExtension.new_for_project(
                                project
                            )
                        ]
                        if with_entry_point_provider
                        else []
                    ),
                    debug,
                    await project.renderer,
                    root_path,
                    job_context=job_context,
                    user=StaticUser(),
                )
                # Build twice, to test with warm caches as well.
                await sut.build()
                webpack_build_directory_path = await sut.build()
            assert (
                webpack_build_directory_path / "css" / "webpack" / "webpack-vendor.css"
            ).exists()
            assert (
                webpack_build_directory_path / "js" / "webpack-entry-loader.js"
            ).exists()
            if with_entry_point_provider:
                async with aiofiles.open(
                    webpack_build_directory_path / "js" / "webpack-entry-loader.js"
                ) as f:
                    webpack_entry_loader_js = await f.read()
                assert f"{root_path}/js/webpack/runtime.js" in webpack_entry_loader_js
                assert (
                    f"{root_path}/js/webpack/{DummyEntryPointProviderExtension.plugin.id}.js"
                    in webpack_entry_loader_js
                )
                assert (
                    webpack_build_directory_path
                    / "js"
                    / "webpack"
                    / f"{DummyEntryPointProviderExtension.plugin.id}.js"
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
            "",
            job_context=job_context,
            user=StaticUser(),
        )
        with pytest.raises(NpmUnavailable):
            await sut.build()
