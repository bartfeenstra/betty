"""Integrate Betty with `Leaflet.js <https://leafletjs.com/>`_."""
from __future__ import annotations

from pathlib import Path

from betty.app.extension import Extension, UserFacingExtension
from betty.extension.webpack import _Webpack, _WebpackEntrypointProvider
from betty.locale import Str


class _Maps(UserFacingExtension, _WebpackEntrypointProvider):
    @classmethod
    def depends_on(cls) -> set[type[Extension]]:
        return {_Webpack}

    @classmethod
    def webpack_entrypoint_directory_path(cls) -> Path:
        return Path(__file__).parent / 'webpack'

    @classmethod
    def label(cls) -> Str:
        return Str._('Maps')

    @classmethod
    def description(cls) -> Str:
        return Str._('Display lists of places as interactive maps using <a href="https://leafletjs.com/">Leaflet</a>.')
