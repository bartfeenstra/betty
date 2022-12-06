import logging
from contextlib import suppress
from pathlib import Path
from shutil import copy2, copytree
from typing import Optional, Set, Type, TYPE_CHECKING, List

from betty.cache import CacheScope

if TYPE_CHECKING:
    from betty.builtins import _

from betty.app.extension import Extension, UserFacingExtension
from betty.generate import Generator
from betty.html import CssProvider, JsProvider
from betty.npm import _Npm, NpmBuilder, npm


class Maps(UserFacingExtension, CssProvider, JsProvider, Generator, NpmBuilder):
    @classmethod
    def depends_on(cls) -> Set[Type[Extension]]:
        return {_Npm}

    async def npm_build(self, working_directory_path: Path, assets_directory_path: Path) -> None:
        await self.app.extensions[_Npm].install(type(self), working_directory_path)
        await npm(('run', 'webpack'), cwd=working_directory_path)
        self._copy_npm_build(working_directory_path / 'webpack-build', assets_directory_path)
        logging.getLogger().info('Built the interactive maps.')

    def _copy_npm_build(self, source_directory_path: Path, destination_directory_path: Path) -> None:
        copy2(source_directory_path / 'maps.css', destination_directory_path / 'maps.css')
        copy2(source_directory_path / 'maps.js', destination_directory_path / 'maps.js')
        with suppress(FileNotFoundError):
            copytree(source_directory_path / 'images', destination_directory_path / 'images')

    @classmethod
    def npm_cache_scope(cls) -> CacheScope:
        return CacheScope.BETTY

    async def generate(self) -> None:
        assets_directory_path = await self.app.extensions[_Npm].ensure_assets(self)
        self._copy_npm_build(assets_directory_path, self.app.project.configuration.www_directory_path)

    @classmethod
    def assets_directory_path(cls) -> Optional[Path]:
        return Path(__file__).parent / 'assets'

    @property
    def public_css_paths(self) -> List[str]:
        return [
            self.app.static_url_generator.generate('maps.css'),
        ]

    @property
    def public_js_paths(self) -> List[str]:
        return [
            self.app.static_url_generator.generate('maps.js'),
        ]

    @classmethod
    def label(cls) -> str:
        return _('Maps')

    @classmethod
    def description(cls) -> str:
        return _('Display lists of places as interactive maps using <a href="https://leafletjs.com/">Leaflet</a>.')
