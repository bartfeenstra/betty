"""Integrate Betty with `Leaflet.js <https://leafletjs.com/>`_."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from betty.app.extension import Extension, UserFacingExtension
from betty.extension.webpack import Webpack, WebpackEntrypointProvider
from betty.locale import Str


class Maps(UserFacingExtension, WebpackEntrypointProvider):
    @classmethod
    def name(cls) -> str:
        return "betty.extension.Maps"

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
        return Str._("Maps")

    @classmethod
    def description(cls) -> Str:
        return Str._(
            'Display lists of places as interactive maps using <a href="https://leafletjs.com/">Leaflet</a>.'
        )
