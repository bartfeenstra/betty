"""
Provide the Documentation API.
"""

import asyncio
import logging
import shutil
from contextlib import suppress, AsyncExitStack
from pathlib import Path
from subprocess import CalledProcessError
from tempfile import TemporaryDirectory

from aiofiles.os import makedirs

from betty import serve
from betty.fs import ROOT_DIRECTORY_PATH
from betty.locale import Str, Localizer
from betty.serve import Server, NoPublicUrlBecauseServerNotStartedError
from betty.subprocess import run_process


async def _build_cache(cache_directory_path: Path) -> Path:
    cache_directory_path /= "docs"
    if not cache_directory_path.exists():
        await _build(cache_directory_path)
    return cache_directory_path


async def _build(output_directory_path: Path) -> None:
    with suppress(FileExistsError):
        await makedirs(output_directory_path)
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
        try:

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
                    "-j",
                    "auto",
                    "-b",
                    "dirhtml",
                    str(source_directory_path),
                    str(output_directory_path),
                ],
                cwd=working_directory_path,
            )
        except CalledProcessError as e:
            if e.stderr is not None:
                logging.getLogger().error(e.stderr)
            raise


class DocumentationServer(Server):
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

    @classmethod
    def label(cls) -> Str:
        return Str._("Betty documentation")

    @property
    def public_url(self) -> str:
        if self._server is not None:
            return self._server.public_url
        raise NoPublicUrlBecauseServerNotStartedError()

    async def start(self) -> None:
        await super().start()
        www_directory_path = await _build_cache(self._cache_directory_path)
        self._server = serve.BuiltinServer(
            www_directory_path, localizer=self._localizer
        )
        await self._exit_stack.enter_async_context(self._server)
        await self.assert_available()

    async def stop(self) -> None:
        await self._exit_stack.aclose()
        await super().stop()
