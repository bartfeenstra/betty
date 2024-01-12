"""Integrate Betty with `ReDoc <https://redocly.com/redoc/>`_."""
from __future__ import annotations

from pathlib import Path

from betty.app.extension import Extension, UserFacingExtension
from betty.extension.webpack import _Webpack
from betty.locale import Str


class _HttpApiDoc(UserFacingExtension):
    @classmethod
    def depends_on(cls) -> set[type[Extension]]:
        return {_Webpack}

    @classmethod
    def assets_directory_path(cls) -> Path | None:
        return Path(__file__).parent / 'assets'

    @classmethod
    def webpack_entrypoint_directory_path(cls) -> Path:
        return Path(__file__).parent / 'webpack'

    @classmethod
    def label(cls) -> Str:
        return Str._('HTTP API Documentation')

    @classmethod
    def description(cls) -> Str:
        return Str._('Display the HTTP API documentation in a user-friendly way using <a href="https://github.com/Redocly/redoc">ReDoc</a>.')
