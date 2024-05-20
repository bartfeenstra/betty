"""Integrate Betty with `ReDoc <https://redocly.com/redoc/>`_."""

from __future__ import annotations

from pathlib import Path

from betty.app.extension import Extension, UserFacingExtension
from betty.extension.webpack import Webpack, WebpackEntrypointProvider
from betty.locale import Str
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence


class HttpApiDoc(UserFacingExtension, WebpackEntrypointProvider):
    @classmethod
    def name(cls) -> str:
        return "betty.extension.HttpApiDoc"

    @classmethod
    def depends_on(cls) -> set[type[Extension]]:
        return {Webpack}

    @classmethod
    def assets_directory_path(cls) -> Path:
        return Path(__file__).parent / "assets"

    @classmethod
    def webpack_entrypoint_directory_path(cls) -> Path:
        return Path(__file__).parent / "webpack"

    def webpack_entrypoint_cache_keys(self) -> Sequence[str]:
        return ()

    @classmethod
    def label(cls) -> Str:
        return Str._("HTTP API Documentation")

    @classmethod
    def description(cls) -> Str:
        return Str._(
            'Display the HTTP API documentation in a user-friendly way using <a href="https://github.com/Redocly/redoc">ReDoc</a>.'
        )
