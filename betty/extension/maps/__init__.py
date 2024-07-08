"""Integrate Betty with `Leaflet.js <https://leafletjs.com/>`_."""

from __future__ import annotations

from pathlib import Path

from typing_extensions import override

from betty.locale.localizable import _, Localizable
from betty.project.extension import Extension, UserFacingExtension
from betty.extension.webpack import Webpack, WebpackEntryPointProvider
from typing import TYPE_CHECKING, final

if TYPE_CHECKING:
    from collections.abc import Sequence


@final
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
    def label(cls) -> Localizable:
        return _("Maps")

    @override
    @classmethod
    def description(cls) -> Localizable:
        return _(
            'Display lists of places as interactive maps using <a href="https://leafletjs.com/">Leaflet</a>.'
        )
