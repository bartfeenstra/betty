from collections.abc import Sequence
from pathlib import Path
from typing import override

import pytest
from pytest_mock import MockerFixture

from betty.job import Context
from betty.npm import NpmUnavailable
from betty.pathlib import StrPath
from betty.project import Project
from betty.service_level import ServiceLevel
from betty.service_provider import ServiceProvider, ServiceProviderDefinition
from betty.service_providers.webpack.build import Builder, EntryPointProvider
from betty.test_utils.user import StaticUser


@ServiceProviderDefinition("dummy", label="-")
class DummyEntryPointProviderServiceProvider(EntryPointProvider, ServiceProvider):
    @override
    @classmethod
    def webpack_entry_point_directory(cls) -> StrPath:
        return Path(__file__).parent / "test_build_webpack_entry_point"

    @override
    def webpack_entry_point_cache_keys(self) -> Sequence[str]:
        return ()


class TestBuilder:
    async def test_build(self, isolated_project: Project, tmp_path: Path) -> None:
        # Loop instead of parameterization, so we can reuse caches.
        for index, (with_entry_point_provider, debug, root_path) in enumerate([
            # With an entry point provider and debug.
            (True, True, ""),
            # With an entry point provider and a root path.
            (True, False, "/root-path"),
            # Without an entry point provider or debug.
            (False, False, ""),
        ]):
            await self._test_build(
                isolated_project,
                tmp_path / str(index),
                with_entry_point_provider,
                debug,
                root_path,
            )

    async def _test_build(
        self,
        isolated_project: Project,
        tmp_path: Path,
        with_entry_point_provider: bool,
        debug: bool,
        root_path: str,
    ) -> None:
        context = Context()
        sut = Builder(
            (
                [DummyEntryPointProviderServiceProvider(services=ServiceLevel())]
                if with_entry_point_provider
                else []
            ),
            debug,
            await isolated_project.jinja,
            root_path,
            user=StaticUser(),
        )
        # Build twice, to test with warm caches as well.
        await sut.build(tmp_path, context=context)
        webpack_build_directory = await sut.build(tmp_path, context=context)
        assert (webpack_build_directory / "css" / "webpack" / "main.css").exists()
        assert (webpack_build_directory / "js" / "webpack-entry-loader.js").exists()
        if with_entry_point_provider:
            with open(
                webpack_build_directory / "js" / "webpack-entry-loader.js",
                encoding="utf-8",
            ) as f:
                webpack_entry_loader_js = f.read()
            assert f"{root_path}/js/webpack/runtime.js" in webpack_entry_loader_js
            assert (
                f"{root_path}/js/webpack/{DummyEntryPointProviderServiceProvider.plugin().id}.js"
                in webpack_entry_loader_js
            )
            assert (
                webpack_build_directory
                / "js"
                / "webpack"
                / f"{DummyEntryPointProviderServiceProvider.plugin().id}.js"
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
