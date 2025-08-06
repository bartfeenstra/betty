"""
Integrate Betty with `Webpack <https://webpack.js.org/>`_.

This module is internal.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from threading import Thread
from typing import TYPE_CHECKING, ClassVar, Self, final

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
from betty.typing import internal, private

if TYPE_CHECKING:
    from collections.abc import Sequence

    from betty.event_dispatcher import EventHandlerRegistry
    from betty.job import Context
    from betty.project import Project


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

    @private
    def __init__(
        self, project: Project, _public_css_path_prefix: str, _public_js_path: str
    ):
        super().__init__(project)
        self._public_css_path_prefix = _public_css_path_prefix
        self._public_js_path = _public_js_path

    @override
    @classmethod
    async def new_for_project(cls, project: Project) -> Self:
        url_generator = await project.url_generator
        return cls(
            project,
            url_generator.generate("betty-static:///css/"),
            url_generator.generate("betty-static:///js/webpack-entry-loader.js"),
        )

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
    @property
    def public_css_paths(self) -> Sequence[str]:
        entry_points: Sequence[EntryPointProvider & Extension] = []

        def _target():
            entry_points.extend(asyncio.run(self._project_entry_point_providers()))

        thread = Thread(target=_target)
        thread.start()
        thread.join()
        return (
            f"{self._public_css_path_prefix}/webpack/webpack-vendor.css",
            *(
                f"{self._public_css_path_prefix}/webpack/{entry_point.plugin_id()}.css"
                for entry_point in entry_points
                if (
                    entry_point.webpack_entry_point_directory_path() / "main.scss"
                ).is_file()
            ),
        )

    @override
    @property
    def public_js_paths(self) -> Sequence[str]:
        return (self._public_js_path,)

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
