from __future__ import annotations

import logging
from pathlib import Path
from shutil import copy2

from aiofiles.os import makedirs

from betty.app.extension import Extension, UserFacingExtension
from betty.cache import CacheScope
from betty.extension.npm import _Npm, NpmBuilder
from betty.generate import Generator, GenerationContext
from betty.locale import Str


class _HttpApiDoc(UserFacingExtension, Generator, NpmBuilder):
    @classmethod
    def depends_on(cls) -> set[type[Extension]]:
        return {_Npm}

    async def npm_build(self, working_directory_path: Path, assets_directory_path: Path) -> None:
        await self.app.extensions[_Npm].install(type(self), working_directory_path)
        copy2(working_directory_path / 'node_modules' / 'redoc' / 'bundles' / 'redoc.standalone.js', assets_directory_path / 'http-api-doc.js')
        logging.getLogger().info(self._app.localizer._('Built the HTTP API documentation.'))

    @classmethod
    def npm_cache_scope(cls) -> CacheScope:
        return CacheScope.BETTY

    async def generate(self, task_context: GenerationContext) -> None:
        assets_directory_path = await self.app.extensions[_Npm].ensure_assets(self)
        await makedirs(self.app.project.configuration.www_directory_path, exist_ok=True)
        copy2(assets_directory_path / 'http-api-doc.js', self.app.project.configuration.www_directory_path / 'http-api-doc.js')

    @classmethod
    def assets_directory_path(cls) -> Path | None:
        return Path(__file__).parent / 'assets'

    @classmethod
    def label(cls) -> Str:
        return Str._('HTTP API Documentation')

    @classmethod
    def description(cls) -> Str:
        return Str._('Display the HTTP API documentation in a user-friendly way using <a href="https://github.com/Redocly/redoc">ReDoc</a>.')
