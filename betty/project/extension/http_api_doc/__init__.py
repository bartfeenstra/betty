"""Integrate Betty with `Swagger UI <https://swagger.io/tools/swagger-ui>`_."""

from __future__ import annotations

from asyncio import to_thread, gather
from pathlib import Path
from shutil import copy2
from typing import TYPE_CHECKING, final

from typing_extensions import override

from betty.locale.localizable import _
from betty.plugin import ShorthandPluginBase
from betty.project.extension.webpack import Webpack
from betty.project.extension.webpack.build import EntryPointProvider
from betty.project.generate import GenerateSiteEvent

if TYPE_CHECKING:
    from betty.project.extension import Extension
    from betty.event_dispatcher import EventHandlerRegistry
    from betty.plugin import PluginIdentifier
    from collections.abc import Sequence


async def _generate_swagger_ui(event: GenerateSiteEvent) -> None:
    await gather(
        to_thread(
            copy2,
            event.job_context._webpack_build_directory_path.parent  # type: ignore[attr-defined]
            / "node_modules"
            / "swagger-ui-dist"
            / "swagger-ui.css",
            event.project.configuration.www_directory_path / "css" / "http-api-doc.css",
        ),
        to_thread(
            copy2,
            event.job_context._webpack_build_directory_path.parent  # type: ignore[attr-defined]
            / "node_modules"
            / "swagger-ui-dist"
            / "swagger-ui-bundle.js",
            event.project.configuration.www_directory_path / "js" / "http-api-doc.js",
        ),
    )


@final
class HttpApiDoc(ShorthandPluginBase, EntryPointProvider):
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
    def register_event_handlers(self, registry: EventHandlerRegistry) -> None:
        registry.add_handler(GenerateSiteEvent, _generate_swagger_ui)

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
