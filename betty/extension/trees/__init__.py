"""Provide interactive family trees by integrating Betty with `Cytoscape.js <https://cytoscape.org/>`_."""

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
class Trees(Extension, WebpackEntryPointProvider):
    """
    Provide interactive family trees for use in web pages.
    """

    @override
    @classmethod
    def plugin_id(cls) -> MachineName:
        return "trees"

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
        return _("Trees")

    @override
    @classmethod
    def plugin_description(cls) -> Localizable:
        return _(
            'Display interactive family trees using <a href="https://cytoscape.org/">Cytoscape</a>.'
        )
