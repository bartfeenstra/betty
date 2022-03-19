import logging
from contextlib import suppress
from pathlib import Path
from shutil import copy2, copytree
from typing import Optional, Iterable, Set, Type, TYPE_CHECKING

from betty.app.extension import Extension
from betty.npm import _Npm, NpmBuilder, npm
from betty.generate import Generator
from betty.gui import GuiBuilder
from betty.html import CssProvider, JsProvider


if TYPE_CHECKING:
    from betty.builtins import _


class Maps(Extension, CssProvider, JsProvider, Generator, GuiBuilder, NpmBuilder):
    @classmethod
    def depends_on(cls) -> Set[Type[Extension]]:
        return {_Npm}

    async def npm_build(self, working_directory_path: Path, assets_directory_path: Path) -> None:
        await self._app.extensions[_Npm].install(type(self), working_directory_path)
        await npm(('run', 'webpack'), cwd=working_directory_path)
        self._copy_npm_build(working_directory_path / 'webpack-build', assets_directory_path)
        logging.getLogger().info('Built the interactive maps.')

    def _copy_npm_build(self, source_directory_path: Path, destination_directory_path: Path) -> None:
        copy2(source_directory_path / 'maps.css', destination_directory_path / 'maps.css')
        copy2(source_directory_path / 'maps.js', destination_directory_path / 'maps.js')
        with suppress(FileNotFoundError):
            copytree(source_directory_path / 'images', destination_directory_path / 'images')

    async def generate(self) -> None:
        assets_directory_path = await self._app.extensions[_Npm].ensure_assets(self)
        self._copy_npm_build(assets_directory_path, self._app.configuration.www_directory_path)

    @classmethod
    def assets_directory_path(cls) -> Optional[Path]:
        return Path(__file__).parent / 'assets'

    @property
    def public_css_paths(self) -> Iterable[str]:
        return {
            self._app.static_url_generator.generate('maps.css'),
        }

    @property
    def public_js_paths(self) -> Iterable[str]:
        return {
            self._app.static_url_generator.generate('maps.js'),
        }

    @classmethod
    def label(cls) -> str:
        return _('Maps')

    @classmethod
    def gui_description(cls) -> str:
        return _('Display lists of places as interactive maps using <a href="https://leafletjs.com/">Leaflet</a>.')
