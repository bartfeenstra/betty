"""
Integrate Betty with `Webpack <https://webpack.js.org/>`_.

This module is internal.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, final

from typing_extensions import override

from betty._npm import NpmRequirement, NpmUnavailable
from betty.html import CssProvider, JsProvider
from betty.jinja2 import ContextVars, Filters, Jinja2Provider
from betty.locale.localizable import static
from betty.os import copy_tree
from betty.plugin import ShorthandPluginBase
from betty.project.extension import Extension
from betty.project.extension.webpack import build
from betty.project.extension.webpack.build import EntryPointProvider
from betty.project.extension.webpack.jinja2.filter import FILTERS
from betty.project.generate import GenerateSiteEvent
from betty.requirement import AllRequirements, Requirement, RequirementError
from betty.typing import internal

if TYPE_CHECKING:
    from collections.abc import Sequence

    from betty.event_dispatcher import EventHandlerRegistry
    from betty.job import Context


async def _generate_assets(event: GenerateSiteEvent) -> None:
    project = event.project
    extensions = await project.extensions
    webpack = extensions[Webpack]
    build_directory_path = await webpack._generate_ensure_build_directory(
        job_context=event.job_context,
    )
    event.job_context._webpack_build_directory_path = build_directory_path  # type: ignore[attr-defined]
    await webpack._copy_build_directory(
        build_directory_path, project.configuration.www_directory_path
    )


@internal
@final
class Webpack(ShorthandPluginBase, Extension, CssProvider, JsProvider, Jinja2Provider):
    """
    Integrate Betty with `Webpack <https://webpack.js.org/>`_.
    """

    _plugin_id = "webpack"
    _plugin_label = static("Webpack")
    _requirement: ClassVar[Requirement | None] = None

    @override
    def register_event_handlers(self, registry: EventHandlerRegistry) -> None:
        registry.add_handler(GenerateSiteEvent, _generate_assets)

    @override
    @classmethod
    async def requirement(cls) -> Requirement:
        if cls._requirement is None:
            cls._requirement = AllRequirements(
                await super().requirement(),
                await NpmRequirement.new(),
            )
        return cls._requirement

    @override
    @classmethod
    def assets_directory_path(cls) -> Path:
        return Path(__file__).parent / "assets"

    @override
    async def get_public_css_paths(self) -> Sequence[str]:
        return (
            "betty-static:///css/webpack-vendor.css",
            *(
                f"betty-static:///css/webpack/{entry_point.plugin_id()}.css"
                for entry_point in await self._project_entry_point_providers()
                if (
                    entry_point.webpack_entry_point_directory_path() / "main.scss"
                ).is_file()
            ),
        )

    @override
    async def get_public_js_paths(self) -> Sequence[str]:
        return ("betty-static:///js/webpack-entry-loader.js",)

    @override
    def new_context_vars(self) -> ContextVars:
        return {
            "webpack_js_entry_points": set(),
        }

    @override
    @property
    def filters(self) -> Filters:
        return FILTERS

    async def _project_entry_point_providers(
        self,
    ) -> Sequence[EntryPointProvider & Extension]:
        extensions = await self._project.extensions
        return [
            extension
            for extension in extensions.flatten()
            if isinstance(extension, EntryPointProvider)
        ]

    async def _new_builder(
        self,
        working_directory_path: Path,
        *,
        job_context: Context,
    ) -> build.Builder:
        return build.Builder(
            working_directory_path,
            await self._project_entry_point_providers(),
            self._project.configuration.debug,
            await self._project.renderer,
            self._project.configuration.root_path,
            job_context=job_context,
            localizer=await self._project.app.localizer,
        )

    async def _copy_build_directory(
        self,
        build_directory_path: Path,
        destination_directory_path: Path,
    ) -> None:
        await copy_tree(build_directory_path, destination_directory_path)

    async def _generate_ensure_build_directory(
        self,
        *,
        job_context: Context,
    ) -> Path:
        builder = await self._new_builder(
            self._project.app.binary_file_cache.with_scope("webpack").path,
            job_context=job_context,
        )
        try:
            # (Re)build the assets if `npm` is available.
            return await builder.build()
        except NpmUnavailable:
            raise RequirementError(await self.requirement()) from None
