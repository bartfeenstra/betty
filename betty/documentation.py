"""
Provide the Documentation API.
"""

import multiprocessing
from asyncio import to_thread
from contextlib import AsyncExitStack
from pathlib import Path
from shutil import copytree
from typing import final

from aiofiles.os import makedirs
from sphinx.application import Sphinx
from typing_extensions import override

from betty import serve
from betty.dirs import ROOT_DIRECTORY_PATH
from betty.serve import NoPublicUrlBecauseServerNotStartedError, Server
from betty.user import User, Verbosity


async def _ensure_www_directory(
    output_directory_path: Path, cache_directory_path: Path, *, user: User
) -> None:
    if not output_directory_path.exists():
        await _build(output_directory_path, cache_directory_path, user=user)


async def _build(
    output_directory_path: Path, cache_directory_path: Path, *, user: User
) -> None:
    await makedirs(output_directory_path, exist_ok=True)
    # sphinx-apidoc must output to the documentation directory, but because we do not want
    # to 'pollute' that with generated files that must not be committed, do our work in a
    # dedicated cache directory.
    source_directory_path = cache_directory_path / "source"
    await to_thread(
        copytree, ROOT_DIRECTORY_PATH / "documentation", source_directory_path
    )
    Sphinx(
        buildername="dirhtml",
        confdir=str(source_directory_path),
        doctreedir=str(cache_directory_path / ".doctrees"),
        outdir=str(output_directory_path),
        parallel=multiprocessing.cpu_count(),
        srcdir=str(source_directory_path),
        verbosity=9 if user.verbosity is Verbosity.MOST_VERBOSE else 0,
    ).build()


@final
class DocumentationServer(Server):
    """
    Serve the documentation site.
    """

    def __init__(self, cache_directory_path: Path, *, user: User):
        super().__init__(user=user)
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
        www_directory_path = self._cache_directory_path / "www"
        await _ensure_www_directory(
            www_directory_path, self._cache_directory_path / "cache", user=self._user
        )
        self._server = serve.BuiltinServer(www_directory_path, user=self._user)
        await self._exit_stack.enter_async_context(self._server)

    @override
    async def stop(self) -> None:
        await self._exit_stack.aclose()
