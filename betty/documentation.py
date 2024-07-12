"""
Provide the Documentation API.
"""

import asyncio
import shutil
from contextlib import AsyncExitStack
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import final

from aiofiles.os import makedirs
from typing_extensions import override

from betty import serve, fs
from betty.fs import ROOT_DIRECTORY_PATH
from betty.locale.localizer import Localizer
from betty.serve import Server, NoPublicUrlBecauseServerNotStartedError
from betty.subprocess import run_process


async def _prebuild_documentation() -> None:
    await _build(fs.PREBUILT_ASSETS_DIRECTORY_PATH / "documentation")


async def _ensure_documentation_directory(cache_directory_path: Path) -> Path:
    if (fs.PREBUILT_ASSETS_DIRECTORY_PATH / "documentation").exists():
        return fs.PREBUILT_ASSETS_DIRECTORY_PATH / "documentation"
    cache_directory_path /= "documentation"
    if not cache_directory_path.exists():
        await _build(cache_directory_path)
    return cache_directory_path


async def _build(output_directory_path: Path) -> None:
    await makedirs(output_directory_path, exist_ok=True)
    with TemporaryDirectory() as working_directory_path_str:
        working_directory_path = Path(working_directory_path_str)
        # sphinx-apidoc must output to the documentation directory, but because we do not want
        # to 'pollute' that with generated files that must not be committed, do our work in a
        # temporary directory and copy the documentation source files there.
        source_directory_path = working_directory_path / "source"
        await asyncio.to_thread(
            shutil.copytree,
            ROOT_DIRECTORY_PATH / "documentation",
            source_directory_path,
        )
        await run_process(
            [
                "sphinx-apidoc",
                "--force",
                "--separate",
                "-d",
                "999",
                "-o",
                str(source_directory_path),
                str(ROOT_DIRECTORY_PATH / "betty"),
                str(ROOT_DIRECTORY_PATH / "betty" / "tests"),
            ],
            cwd=working_directory_path,
        )
        await run_process(
            [
                "sphinx-build",
                "-b",
                "dirhtml",
                "-j",
                "auto",
                str(source_directory_path),
                str(output_directory_path),
            ],
            cwd=working_directory_path,
        )


@final
class DocumentationServer(Server):
    """
    Serve the documentation site.
    """

    def __init__(
        self,
        cache_directory_path: Path,
        *,
        localizer: Localizer,
    ):
        super().__init__(localizer)
        self._cache_directory_path = cache_directory_path
        self._server: Server | None = None
        self._exit_stack = AsyncExitStack()

    @override
    @property
    def public_url(self) -> str:
        if self._server is not None:
            return self._server.public_url
        raise NoPublicUrlBecauseServerNotStartedError()

    @override
    async def start(self) -> None:
        await super().start()
        www_directory_path = await _ensure_documentation_directory(
            self._cache_directory_path
        )
        self._server = serve.BuiltinServer(
            www_directory_path, localizer=self._localizer
        )
        await self._exit_stack.enter_async_context(self._server)
        await self.assert_available()

    @override
    async def stop(self) -> None:
        await self._exit_stack.aclose()
        await super().stop()
