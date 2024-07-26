"""Integrate Betty with `Leaflet.js <https://leafletjs.com/>`_."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, final

from typing_extensions import override

from betty.extension.webpack import Webpack, WebpackEntryPointProvider
from betty.locale.localizable import _, Localizable
from betty.project.extension import Extension

if TYPE_CHECKING:
    from betty.machine_name import MachineName
    from collections.abc import Sequence


@final
class Maps(Extension, WebpackEntryPointProvider):
    """
    Provide interactive maps for use on web pages.
    """

    @override
    @classmethod
    def plugin_id(cls) -> MachineName:
        return "maps"

    @override
    @classmethod
    def depends_on(cls) -> set[MachineName]:
        return {Webpack.plugin_id()}

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
    def plugin_label(cls) -> Localizable:
        return _("Maps")

    @override
    @classmethod
    def plugin_description(cls) -> Localizable:
        return _(
            'Display lists of places as interactive maps using <a href="https://leafletjs.com/">Leaflet</a>.'
        )
