import logging
from pathlib import Path
from shutil import copy2
from typing import Optional, Set, Type, TYPE_CHECKING


if TYPE_CHECKING:
    from betty.builtins import _

from betty.app.extension import Extension, UserFacingExtension
from betty.generate import Generator
from betty.npm import _Npm, NpmBuilder


class HttpApiDoc(UserFacingExtension, Generator, NpmBuilder):
    @classmethod
    def depends_on(cls) -> Set[Type[Extension]]:
        return {_Npm}

    async def npm_build(self, working_directory_path: Path, assets_directory_path: Path) -> None:
        await self.app.extensions[_Npm].install(type(self), working_directory_path)
        copy2(working_directory_path / 'node_modules' / 'redoc' / 'bundles' / 'redoc.standalone.js', assets_directory_path / 'http-api-doc.js')
        logging.getLogger().info('Built the HTTP API documentation.')

    async def generate(self) -> None:
        assets_directory_path = await self.app.extensions[_Npm].ensure_assets(self)
        copy2(assets_directory_path / 'http-api-doc.js', self.app.project.configuration.www_directory_path / 'http-api-doc.js')

    @classmethod
    def assets_directory_path(cls) -> Optional[Path]:
        return Path(__file__).parent / 'assets'

    @classmethod
    def label(cls) -> str:
        return 'HTTP API Documentation'

    @classmethod
    def description(cls) -> str:
        return _('Display the HTTP API documentation in a user-friendly way using <a href="https://github.com/Redocly/redoc">ReDoc</a>.')
