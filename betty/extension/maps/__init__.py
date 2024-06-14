"""Integrate Betty with `Leaflet.js <https://leafletjs.com/>`_."""

from __future__ import annotations

from pathlib import Path

from typing_extensions import override

from betty.app.extension import Extension, UserFacingExtension
from betty.extension.webpack import Webpack, WebpackEntryPointProvider
from betty.locale import Str
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence


class Maps(UserFacingExtension, WebpackEntryPointProvider):
    """
    Provide interactive maps for use on web pages.
    """

    @override
    @classmethod
    def name(cls) -> str:
        return "betty.extension.Maps"

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
        return Str._("Maps")

    @override
    @classmethod
    def description(cls) -> Str:
        return Str._(
            'Display lists of places as interactive maps using <a href="https://leafletjs.com/">Leaflet</a>.'
        )
