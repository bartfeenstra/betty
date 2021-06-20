import hashlib
import logging
import shutil
import sys
from contextlib import suppress
from pathlib import Path
from typing import Optional

from betty import subprocess
from betty.fs import DirectoryBackup
from betty.generate import Generator
from betty.extension import Extension
from betty.app import App, AppAwareFactory


class ReDoc(Extension, AppAwareFactory, Generator):
    def __init__(self, app: App):
        self._app = app

    @classmethod
    def new_for_app(cls, app: App, *args, **kwargs):
        return cls(app)

    async def generate(self) -> None:
        await self._render()

    @property
    def assets_directory_path(self) -> Optional[Path]:
        return Path(__file__).parent / 'assets'

    async def _render(self) -> None:
        build_directory_path = self._app.configuration.cache_directory_path / self.name() / hashlib.md5(str(self.assets_directory_path).encode()).hexdigest() / 'build'

        async with DirectoryBackup(build_directory_path, 'node_modules'):
            with suppress(FileNotFoundError):
                shutil.rmtree(build_directory_path)
            shutil.copytree(self.assets_directory_path / 'js', build_directory_path)
        await self._app.renderer.render_tree(build_directory_path)

        self._app.executor.submit(_do_render, build_directory_path, self._app.configuration.www_directory_path)


def _do_render(build_directory_path: Path, www_directory_path: Path) -> None:
    # Use a shell on Windows so subprocess can find the executables it needs (see https://bugs.python.org/issue17023).
    shell = sys.platform.startswith('win32')

    # Install third-party dependencies.
    subprocess.run(['npm', 'install', '--production'], cwd=build_directory_path, shell=shell)

    shutil.copy2(build_directory_path / 'node_modules' / 'redoc' / 'bundles' / 'redoc.standalone.js', www_directory_path / 'redoc.js')

    logging.getLogger().info('Built the ReDoc API documentation.')
