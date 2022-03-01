import logging
import subprocess
from pathlib import Path
from shutil import copy2
from typing import Optional, Iterable, Set, Type

from betty.app.extension import Extension
from betty.npm import _Npm, NpmBuilder, npm
from betty.generate import Generator
from betty.gui import GuiBuilder
from betty.html import CssProvider, JsProvider


class Trees(Extension, CssProvider, JsProvider, Generator, GuiBuilder, NpmBuilder):
    @classmethod
    def depends_on(cls) -> Set[Type[Extension]]:
        return {_Npm}

    async def npm_build(self, working_directory_path: Path, assets_directory_path: Path) -> None:
        await self._app.extensions[_Npm].install(type(self), working_directory_path)
        await npm(('run', 'webpack'), cwd=working_directory_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self._copy_npm_build(working_directory_path / 'webpack-build', assets_directory_path)
        logging.getLogger().info('Built the interactive family trees.')

    def _copy_npm_build(self, source_directory_path: Path, destination_directory_path: Path) -> None:
        copy2(source_directory_path / 'trees.css', destination_directory_path / 'trees.css')
        copy2(source_directory_path / 'trees.js', destination_directory_path / 'trees.js')

    async def generate(self) -> None:
        assets_directory_path = await self._app.extensions[_Npm].ensure_assets(self)
        self._copy_npm_build(assets_directory_path, self._app.configuration.www_directory_path)

    @classmethod
    def assets_directory_path(cls) -> Optional[Path]:
        return Path(__file__).parent / 'assets'

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
