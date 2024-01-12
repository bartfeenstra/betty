"""Provide interactive family trees by integrating Betty with `Cytoscape.js <https://cytoscape.org/>`_."""
from __future__ import annotations

from pathlib import Path

from betty.app.extension import Extension, UserFacingExtension
from betty.extension.webpack import _Webpack, _WebpackEntrypointProvider
from betty.locale import Str


class _Trees(UserFacingExtension, _WebpackEntrypointProvider):
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
        return Str._('Trees')

    @classmethod
    def description(cls) -> Str:
        return Str._('Display interactive family trees using <a href="https://cytoscape.org/">Cytoscape</a>.')
