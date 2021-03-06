import hashlib
import logging
import shutil
import sys
from contextlib import suppress
from os import path
from os.path import dirname
from typing import Optional, Iterable

from betty import subprocess
from betty.fs import DirectoryBackup
from betty.generate import Generator
from betty.html import HtmlProvider
from betty.extension import Extension
from betty.app import App, AppAwareFactory


class Trees(Extension, AppAwareFactory, HtmlProvider, Generator):
    def __init__(self, app: App):
        self._app = app

    @classmethod
    def new_for_app(cls, app: App, *args, **kwargs):
        return cls(app)

    async def generate(self) -> None:
        await self._render()

    @property
    def assets_directory_path(self) -> Optional[str]:
        return '%s/assets' % dirname(__file__)

    async def _render(self) -> None:
        build_directory_path = path.join(self._app.configuration.cache_directory_path, self.name(),
                                         hashlib.md5(self.assets_directory_path.encode()).hexdigest(), 'build')

        async with DirectoryBackup(build_directory_path, 'node_modules'):
            with suppress(FileNotFoundError):
                shutil.rmtree(build_directory_path)
            shutil.copytree(path.join(self.assets_directory_path, 'js'), build_directory_path)
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


def _do_render(build_directory_path: str, www_directory_path: str) -> None:
    # Use a shell on Windows so subprocess can find the executables it needs (see https://bugs.python.org/issue17023).
    shell = sys.platform.startswith('win32')

    # Install third-party dependencies.
    subprocess.run(['npm', 'install', '--production'], cwd=build_directory_path, shell=shell)

    # Run Webpack.
    subprocess.run(['npm', 'run', 'webpack'], cwd=build_directory_path, shell=shell)
    output_directory_path = path.join(path.dirname(build_directory_path), 'output')
    shutil.copy2(path.join(output_directory_path, 'trees.css'), path.join(www_directory_path, 'trees.css'))
    shutil.copy2(path.join(output_directory_path, 'trees.js'), path.join(www_directory_path, 'trees.js'))

    logging.getLogger().info('Built the interactive family trees.')
