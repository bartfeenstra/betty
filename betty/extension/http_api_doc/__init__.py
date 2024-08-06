"""Integrate Betty with `Swagger UI <https://swagger.io/tools/swagger-ui>`_."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, final

from betty.extension.webpack import Webpack, WebpackEntryPointProvider
from betty.locale.localizable import _, Localizable
from betty.project.extension import Extension
from typing_extensions import override

if TYPE_CHECKING:
    from betty.machine_name import MachineName
    from collections.abc import Sequence


@final
class HttpApiDoc(Extension, WebpackEntryPointProvider):
    """
    Provide user-friendly HTTP API documentation.
    """

    @override
    @classmethod
    def plugin_id(cls) -> MachineName:
        return "http-api-doc"

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
        return _("HTTP API Documentation")

    @override
    @classmethod
    def plugin_description(cls) -> Localizable:
        return _(
            'Display the HTTP API documentation in a user-friendly way using <a href="https://swagger.io/tools/swagger-ui">Swagger UI</a>.'
        )
