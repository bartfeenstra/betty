import asyncio
import logging
import os
import shutil
from contextlib import suppress, AsyncExitStack
from pathlib import Path
from subprocess import CalledProcessError
from tempfile import TemporaryDirectory

from betty import subprocess, serve
from betty.locale import Str, Localizer
from betty.serve import Server, NoPublicUrlBecauseServerNotStartedError


async def _build_cache(cache_directory_path: Path) -> Path:
    cache_directory_path /= 'docs'
    if not cache_directory_path.exists():
        await _build(cache_directory_path)
    return cache_directory_path


async def _build(output_directory_path: Path) -> None:
    with suppress(FileExistsError):
        await asyncio.to_thread(os.makedirs, output_directory_path)
    with TemporaryDirectory() as working_directory_path:
        source_directory_path = Path(working_directory_path) / 'source'
        await asyncio.to_thread(shutil.copytree, Path(__file__).parent.parent / 'documentation', source_directory_path)
        await asyncio.to_thread(shutil.copy2, Path(__file__).parent.parent / 'betty' / 'assets' / 'public' / 'static' / 'betty-32x32.png', source_directory_path / 'betty-logo.png')
        try:
            await subprocess.run_exec(['sphinx-apidoc', '--force', '--separate', '-d', '999', '-o', str(source_directory_path), 'betty', 'betty/tests'])
            await subprocess.run_exec(['sphinx-build', str(source_directory_path), str(output_directory_path)])
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
        return Str._('Betty documentation')

    @property
    def public_url(self) -> str:
        if self._server is not None:
            return self._server.public_url
        raise NoPublicUrlBecauseServerNotStartedError()

    async def start(self) -> None:
        await super().start()
        try:
            www_directory_path = await _build_cache(self._cache_directory_path)
            self._server = serve.BuiltinServer(www_directory_path, localizer=self._localizer)
            await self._exit_stack.enter_async_context(self._server)
        except BaseException:
            await self.stop()
            raise

    async def stop(self) -> None:
        await self._exit_stack.aclose()
        await super().stop()
