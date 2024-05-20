"""Provide interactive family trees by integrating Betty with `Cytoscape.js <https://cytoscape.org/>`_."""

from __future__ import annotations

from pathlib import Path

from betty.app.extension import Extension, UserFacingExtension
from betty.extension.webpack import Webpack, WebpackEntrypointProvider
from betty.locale import Str
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence


class Trees(UserFacingExtension, WebpackEntrypointProvider):
    @classmethod
    def name(cls) -> str:
        return "betty.extension.Trees"

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
        return Str._("Trees")

    @classmethod
    def description(cls) -> Str:
        return Str._(
            'Display interactive family trees using <a href="https://cytoscape.org/">Cytoscape</a>.'
        )
