"""Integrate Betty with `Swagger UI <https://swagger.io/tools/swagger-ui>`_."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, final

from typing_extensions import override

from betty.html import NavigationLink, NavigationLinkProvider
from betty.locale.localizable import _
from betty.plugin import ShorthandPluginBase
from betty.project.extension.webpack import Webpack
from betty.project.extension.webpack.build import EntryPointProvider

if TYPE_CHECKING:
    from collections.abc import Sequence

    from betty.plugin import PluginIdentifier
    from betty.project.extension import Extension


@final
class HttpApiDoc(ShorthandPluginBase, EntryPointProvider, NavigationLinkProvider):
    """
    Provide user-friendly HTTP API documentation.
    """

    _plugin_id = "http-api-doc"
    _plugin_label = _("HTTP API Documentation")
    _plugin_description = _(
        'Display the HTTP API documentation in a user-friendly way using <a href="https://swagger.io/tools/swagger-ui">Swagger UI</a>.'
    )

    @override
    @classmethod
    def depends_on(cls) -> set[PluginIdentifier[Extension]]:
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
    def secondary_navigation_links(self) -> Sequence[NavigationLink]:
        return [
            NavigationLink("betty-static:///api/index.html", _("API documentation")),
        ]
