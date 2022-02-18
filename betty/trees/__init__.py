import hashlib
import logging
import shutil
import sys
from contextlib import suppress
from pathlib import Path
from typing import Optional, Iterable

from betty import subprocess
from betty.app.extension import Extension
from betty.fs import DirectoryBackup
from betty.generate import Generator
from betty.gui import GuiBuilder
from betty.html import CssProvider, JsProvider


class Trees(Extension, CssProvider, JsProvider, Generator, GuiBuilder):
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

    @property
    def public_css_paths(self) -> Iterable[str]:
        return {
            self._app.static_url_generator.generate('trees.css'),
        }

    @property
    def public_js_paths(self) -> Iterable[str]:
        return {
            self._app.static_url_generator.generate('trees.js'),
        }

    @classmethod
    def gui_name(cls) -> str:
        return _('Trees')

    @classmethod
    def gui_description(cls) -> str:
        return _('Display interactive family trees using <a href="https://cytoscape.org/">Cytoscape</a>.')


def _do_render(build_directory_path: Path, www_directory_path: Path) -> None:
    # Use a shell on Windows so subprocess can find the executables it needs (see https://bugs.python.org/issue17023).
    shell = sys.platform.startswith('win32')

    # Install third-party dependencies.
    subprocess.run(['npm', 'install', '--production'], cwd=build_directory_path, shell=shell)

    # Run Webpack.
    subprocess.run(['npm', 'run', 'webpack'], cwd=build_directory_path, shell=shell)
    output_directory_path = build_directory_path.parent / 'output'
    shutil.copy2(output_directory_path / 'trees.css', www_directory_path / 'trees.css')
    shutil.copy2(output_directory_path / 'trees.js', www_directory_path / 'trees.js')

    logging.getLogger().info('Built the interactive family trees.')
