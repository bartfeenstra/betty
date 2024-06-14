"""Integrate Betty with `ReDoc <https://redocly.com/redoc/>`_."""

from __future__ import annotations

from pathlib import Path

from typing_extensions import override

from betty.app.extension import Extension, UserFacingExtension
from betty.extension.webpack import Webpack, WebpackEntryPointProvider
from betty.locale import Str
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence


class HttpApiDoc(UserFacingExtension, WebpackEntryPointProvider):
    """
    Provide user-friendly HTTP API documentation.
    """

    @override
    @classmethod
    def name(cls) -> str:
        return "betty.extension.HttpApiDoc"

    @override
    @classmethod
    def depends_on(cls) -> set[type[Extension]]:
        return {Webpack}

    @override
    @classmethod
    def assets_directory_path(cls) -> Path:
        return Path(__file__).parent / "assets"

    @override
    @classmethod
    def webpack_entry_point_directory_path(cls) -> Path:
        return Path(__file__).parent / "webpack"

    @override
    def webpack_entry_point_cache_keys(self) -> Sequence[str]:
        return ()

    @override
    @classmethod
    def label(cls) -> Str:
        return Str._("HTTP API Documentation")

    @override
    @classmethod
    def description(cls) -> Str:
        return Str._(
            'Display the HTTP API documentation in a user-friendly way using <a href="https://github.com/Redocly/redoc">ReDoc</a>.'
        )
