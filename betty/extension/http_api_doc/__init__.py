"""Integrate Betty with `ReDoc <https://redocly.com/redoc/>`_."""

from __future__ import annotations

from asyncio import to_thread
from pathlib import Path
from shutil import copy
from typing import TYPE_CHECKING, final

from betty.generate import GenerateSiteEvent
from typing_extensions import override

from betty.extension.webpack import Webpack, WebpackEntryPointProvider
from betty.locale.localizable import _, Localizable
from betty.project.extension import Extension

if TYPE_CHECKING:
    from betty.event_dispatcher import EventHandlerRegistry
    from betty.machine_name import MachineName
    from collections.abc import Sequence


async def _generate_assets(event: GenerateSiteEvent) -> None:
    webpack = event.project.extensions[Webpack.plugin_id()]
    assert isinstance(webpack, Webpack)
    webpack_build_directory_path: Path = event.job_context._webpack_build_directory_path
    npm_install_directory_path = webpack_build_directory_path.parent
    # The HttpApiDoc extension does not have a Webpack build as such (yet), but simply
    # requires a single dependency distribution asset verbatim.
    await to_thread(
        copy,
        npm_install_directory_path
        / "node_modules"
        / "redoc"
        / "bundles"
        / "redoc.standalone.js",
        event.project.configuration.www_directory_path / "js" / "http-api-doc.js",
    )


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
            'Display the HTTP API documentation in a user-friendly way using <a href="https://github.com/Redocly/redoc">ReDoc</a>.'
        )

    @override
    def register_event_handlers(self, registry: EventHandlerRegistry) -> None:
        registry.add_handler(GenerateSiteEvent, _generate_assets)
