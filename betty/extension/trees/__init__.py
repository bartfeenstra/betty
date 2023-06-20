from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from shutil import copy2

from betty.app.extension import Extension, UserFacingExtension
from betty.cache import CacheScope
from betty.generate import Generator
from betty.html import CssProvider, JsProvider
from betty.locale import Localizer
from betty.extension.npm import _Npm, NpmBuilder, npm


class _Trees(UserFacingExtension, CssProvider, JsProvider, Generator, NpmBuilder):
    @classmethod
    def depends_on(cls) -> set[type[Extension]]:
        return {_Npm}

    async def npm_build(self, working_directory_path: Path, assets_directory_path: Path) -> None:
        await self.app.extensions[_Npm].install(type(self), working_directory_path)
        await npm(('run', 'webpack'), cwd=working_directory_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self._copy_npm_build(working_directory_path / 'webpack-build', assets_directory_path)
        logging.getLogger().info(self.app.localizer._('Built the interactive family trees.'))

    def _copy_npm_build(self, source_directory_path: Path, destination_directory_path: Path) -> None:
        destination_directory_path.mkdir(parents=True, exist_ok=True)
        copy2(source_directory_path / 'trees.css', destination_directory_path / 'trees.css')
        copy2(source_directory_path / 'trees.js', destination_directory_path / 'trees.js')

    @classmethod
    def npm_cache_scope(cls) -> CacheScope:
        return CacheScope.BETTY

    async def generate(self) -> None:
        assets_directory_path = await self.app.extensions[_Npm].ensure_assets(self)
        self._copy_npm_build(assets_directory_path, self.app.static_www_directory_path)

    @classmethod
    def assets_directory_path(cls) -> Path | None:
        return Path(__file__).parent / 'assets'

    @property
    def public_css_paths(self) -> list[str]:
        return [
            self.app.static_url_generator.generate('trees.css'),
        ]

    @property
    def public_js_paths(self) -> list[str]:
        return [
            self.app.static_url_generator.generate('trees.js'),
        ]

    @classmethod
    def label(cls, localizer: Localizer) -> str:
        return localizer._('Trees')

    @classmethod
    def description(cls, localizer: Localizer) -> str:
        return localizer._('Display interactive family trees using <a href="https://cytoscape.org/">Cytoscape</a>.')
