"""
Provide the Documentation API.
"""

from asyncio import to_thread
from contextlib import AsyncExitStack
from pathlib import Path
from shutil import copytree
from tempfile import TemporaryDirectory
from typing import final

from aiofiles.os import makedirs
from typing_extensions import override

from betty import serve
from betty.dirs import ROOT_DIRECTORY_PATH
from betty.serve import NoPublicUrlBecauseServerNotStartedError, Server
from betty.subprocess import run_process
from betty.user import User


async def _ensure_documentation_directory(
    cache_directory_path: Path, *, user: User
) -> Path:
    cache_directory_path /= "documentation"
    if not cache_directory_path.exists():
        await _build(cache_directory_path, user=user)
    return cache_directory_path


async def _build(output_directory_path: Path, *, user: User) -> None:
    await makedirs(output_directory_path, exist_ok=True)
    with TemporaryDirectory() as working_directory_path_str:
        working_directory_path = Path(working_directory_path_str)
        # sphinx-apidoc must output to the documentation directory, but because we do not want
        # to 'pollute' that with generated files that must not be committed, do our work in a
        # temporary directory and copy the documentation source files there.
        source_directory_path = working_directory_path / "source"
        await to_thread(
            copytree, ROOT_DIRECTORY_PATH / "documentation", source_directory_path
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
            user=user,
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
            user=user,
        )


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
        www_directory_path = await _ensure_documentation_directory(
            self._cache_directory_path, user=self._user
        )
        self._server = serve.BuiltinServer(www_directory_path, user=self._user)
        await self._exit_stack.enter_async_context(self._server)

    @override
    async def stop(self) -> None:
        await self._exit_stack.aclose()
