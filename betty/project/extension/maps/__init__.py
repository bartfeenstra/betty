"""Integrate Betty with `Leaflet.js <https://leafletjs.com/>`_."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, final

from typing_extensions import override

from betty.locale.localizable import _
from betty.plugin import ShorthandPluginBase
from betty.project.extension.webpack import Webpack
from betty.project.extension.webpack.build import EntryPointProvider

if TYPE_CHECKING:
    from betty.project.extension import Extension
    from betty.plugin import PluginIdentifier
    from collections.abc import Sequence


@final
class Maps(ShorthandPluginBase, EntryPointProvider):
    """
    Provide interactive maps for use on web pages.
    """

    _plugin_id = "maps"
    _plugin_label = _("Maps")
    _plugin_description = _(
        'Display lists of places as interactive maps using <a href="https://leafletjs.com/">Leaflet</a>.'
    )

    @override
    @classmethod
    def depends_on(cls) -> set[PluginIdentifier[Extension]]:
        return {Webpack}

    @override
    @classmethod
    def webpack_entry_point_directory_path(cls) -> Path:
        return Path(__file__).parent / "webpack"

    @override
    def webpack_entry_point_cache_keys(self) -> Sequence[str]:
        return ()
