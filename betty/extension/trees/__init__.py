"""Provide interactive family trees by integrating Betty with `Cytoscape.js <https://cytoscape.org/>`_."""

from __future__ import annotations

from pathlib import Path

from typing_extensions import override

from betty.app.extension import Extension, UserFacingExtension
from betty.extension.webpack import Webpack, WebpackEntryPointProvider
from betty.locale import Str, Localizable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence


class Trees(UserFacingExtension, WebpackEntryPointProvider):
    """
    Provide interactive family trees for use in web pages.
    """

    @override
    @classmethod
    def name(cls) -> str:
        return "betty.extension.Trees"

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
    def label(cls) -> Localizable:
        return Str._("Trees")

    @override
    @classmethod
    def description(cls) -> Localizable:
        return Str._(
            'Display interactive family trees using <a href="https://cytoscape.org/">Cytoscape</a>.'
        )
