from collections.abc import Sequence
from pathlib import Path
from typing import override

import aiofiles
import pytest
from pytest_mock import MockerFixture

from betty.app import App
from betty.extension import Extension, ExtensionDefinition
from betty.extension.webpack.build import Builder, EntryPointProvider
from betty.job import Context
from betty.npm import NpmUnavailable
from betty.project import Project
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE
from betty.test_utils.user import StaticUser


@ExtensionDefinition("dummy", label=DUMMY_LOCALIZABLE)
class DummyEntryPointProviderExtension(EntryPointProvider, Extension):
    @override
    @classmethod
    def webpack_entry_point_directory_path(cls) -> Path:
        return Path(__file__).parent / "test_build_webpack_entry_point"

    @override
    def webpack_entry_point_cache_keys(self) -> Sequence[str]:
        return ()


class TestBuilder:
    async def test_build(self, isolated_app: App, tmp_path: Path) -> None:
        with ExtensionDefinition.type().discoverer.override():
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
                    isolated_app,
                    tmp_path / str(index),
                    with_entry_point_provider,
                    debug,
                    root_path,
                )

    async def _test_build(
        self,
        isolated_app: App,
        tmp_path: Path,
        with_entry_point_provider: bool,
        debug: bool,
        root_path: str,
    ) -> None:
        async with Project.new_isolated(isolated_app) as project:
            context = Context()
            async with project:
                sut = Builder(
                    (
                        [DummyEntryPointProviderExtension(services=project)]
                        if with_entry_point_provider
                        else []
                    ),
                    debug,
                    await project.jinja,
                    root_path,
                    user=StaticUser(),
                )
                # Build twice, to test with warm caches as well.
                await sut.build(tmp_path, context=context)
                webpack_build_directory_path = await sut.build(
                    tmp_path, context=context
                )
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
                    f"{root_path}/js/webpack/{DummyEntryPointProviderExtension.plugin().id}.js"
                    in webpack_entry_loader_js
                )
                assert (
                    webpack_build_directory_path
                    / "js"
                    / "webpack"
                    / f"{DummyEntryPointProviderExtension.plugin().id}.js"
                ).exists()

    async def test_build_with_npm_unavailable(
        self, mocker: MockerFixture, tmp_path: Path
    ) -> None:
        m_npm = mocker.patch("betty.npm.npm")
        m_npm.side_effect = NpmUnavailable()

        context = Context()
        m_jinja = mocker.AsyncMock()
        sut = Builder(
            [],
            False,
            m_jinja,
            "",
            user=StaticUser(),
        )
        with pytest.raises(NpmUnavailable):
            await sut.build(tmp_path, context=context)
