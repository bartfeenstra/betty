"""
Integrate Betty with `Webpack <https://webpack.js.org/>`_.

This module is internal.
"""

from __future__ import annotations

from abc import abstractmethod, ABC
from pathlib import Path
from typing import TYPE_CHECKING, final, Self

from aiofiles.tempfile import TemporaryDirectory
from typing_extensions import override

from betty import fs
from betty._npm import NpmRequirement, NpmUnavailable
from betty.app import App
from betty.html import CssProvider
from betty.jinja2 import Jinja2Provider, Filters, ContextVars
from betty.job import Context
from betty.locale.localizable import _, Localizable, static
from betty.os import copy_tree
from betty.plugin import ShorthandPluginBase
from betty.project import Project, extension
from betty.project.extension import Extension
from betty.project.extension.webpack import build
from betty.project.extension.webpack.build import webpack_build_id
from betty.project.extension.webpack.jinja2.filter import FILTERS
from betty.project.generate import GenerateSiteEvent
from betty.requirement import (
    Requirement,
    AllRequirements,
    AnyRequirement,
    RequirementError,
)
from betty.typing import internal

if TYPE_CHECKING:
    from betty.event_dispatcher import EventHandlerRegistry
    from collections.abc import Sequence


def _prebuilt_webpack_build_directory_path(
    entry_point_providers: Sequence[WebpackEntryPointProvider & Extension], debug: bool
) -> Path:
    return (
        fs.PREBUILT_ASSETS_DIRECTORY_PATH
        / "webpack"
        / f"build-{webpack_build_id(entry_point_providers, debug)}"
    )


async def _prebuild_webpack_assets() -> None:
    """
    Prebuild Webpack assets for inclusion in package builds.
    """
    async with App.new_temporary() as app, app:
        job_context = Context()
        async with Project.new_temporary(app) as project:
            project.configuration.extensions.enable(Webpack)
            project.configuration.extensions.enable(
                *(
                    await extension.EXTENSION_REPOSITORY.select(
                        WebpackEntryPointProvider  # type: ignore[type-abstract]
                    )
                )
            )
            async with project:
                extensions = await project.extensions
                webpack = extensions[Webpack]
                await webpack.prebuild(job_context=job_context)


class WebpackEntryPointProvider(ABC):
    """
    An extension that provides Webpack entry points.
    """

    @classmethod
    @abstractmethod
    def webpack_entry_point_directory_path(cls) -> Path:
        """
        Get the path to the directory with the entry point assets.

        The directory must include at least a ``package.json`` and ``main.ts``.
        """
        pass

    @abstractmethod
    def webpack_entry_point_cache_keys(self) -> Sequence[str]:
        """
        Get the keys that make a Webpack build for this provider unique.

        Providers that can be cached regardless may ``return ()``.
        """
        pass


class PrebuiltAssetsRequirement(Requirement):
    """
    Check if prebuilt assets are available.
    """

    @override
    async def is_met(self) -> bool:
        return (fs.PREBUILT_ASSETS_DIRECTORY_PATH / "webpack").is_dir()

    @override
    async def summary(self) -> Localizable:
        return (
            _("Pre-built Webpack front-end assets are available")
            if await self.is_met()
            else _("Pre-built Webpack front-end assets are unavailable")
        )


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
class Webpack(ShorthandPluginBase, Extension, CssProvider, Jinja2Provider):
    """
    Integrate Betty with `Webpack <https://webpack.js.org/>`_.
    """

    _npm_requirement = NpmRequirement()
    _prebuilt_assets_requirement = PrebuiltAssetsRequirement()
    _requirement = AnyRequirement(
        _npm_requirement,
        _prebuilt_assets_requirement,
    )

    _plugin_id = "webpack"
    _plugin_label = static("Webpack")

    @internal
    def __init__(self, project: Project, public_css_paths: Sequence[str]):
        super().__init__(project)
        self._public_css_paths = public_css_paths

    @override
    @classmethod
    async def new_for_project(cls, project: Project) -> Self:
        static_url_generator = await project.static_url_generator
        return cls(project, [static_url_generator.generate("/css/vendor.css")])

    @override
    def register_event_handlers(self, registry: EventHandlerRegistry) -> None:
        registry.add_handler(GenerateSiteEvent, _generate_assets)

    @override
    @classmethod
    def enable_requirement(cls) -> Requirement:
        return AllRequirements(super().enable_requirement(), cls._requirement)

    def build_requirement(self) -> Requirement:
        """
        Get the requirement that must be satisfied for Webpack builds to be available.
        """
        return self._npm_requirement

    @override
    @classmethod
    def assets_directory_path(cls) -> Path:
        return Path(__file__).parent / "assets"

    @override
    @property
    def public_css_paths(self) -> Sequence[str]:
        return self._public_css_paths

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
    ) -> Sequence[WebpackEntryPointProvider & Extension]:
        extensions = await self._project.extensions
        return [
            extension
            for extension in extensions.flatten()
            if isinstance(extension, WebpackEntryPointProvider)
        ]

    async def prebuild(self, job_context: Context) -> None:
        """
        Prebuild the Webpack assets.
        """
        async with TemporaryDirectory() as working_directory_path_str:
            builder = await self._new_builder(
                Path(working_directory_path_str),
                job_context=job_context,
            )
            build_directory_path = await builder.build()
            await self._copy_build_directory(
                build_directory_path,
                _prebuilt_webpack_build_directory_path(
                    await self._project_entry_point_providers(), False
                ),
            )

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
            pass

        # Use prebuilt assets if they exist.
        prebuilt_webpack_build_directory_path = _prebuilt_webpack_build_directory_path(
            await self._project_entry_point_providers(),
            self._project.configuration.debug,
        )
        if prebuilt_webpack_build_directory_path.exists():
            return prebuilt_webpack_build_directory_path

        raise RequirementError(self._requirement)
