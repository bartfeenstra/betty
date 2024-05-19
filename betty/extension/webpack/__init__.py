"""
Integrate Betty with `Webpack <https://webpack.js.org/>`_.

This module is internal.
"""

from __future__ import annotations

from asyncio import to_thread
from collections.abc import Callable, Sequence
from pathlib import Path
from shutil import copytree
from typing import Any

from aiofiles.tempfile import TemporaryDirectory

from betty import fs
from betty._npm import NpmRequirement, NpmUnavailable
from betty.app import App
from betty.app.extension import Extension, discover_extension_types
from betty.extension.webpack import build
from betty.extension.webpack.build import webpack_build_id
from betty.extension.webpack.jinja2.filter import FILTERS
from betty.generate import Generator, GenerationContext
from betty.html import CssProvider
from betty.jinja2 import Jinja2Provider
from betty.job import Context
from betty.locale import Str
from betty.project import Project, ProjectConfiguration
from betty.requirement import (
    Requirement,
    AllRequirements,
    AnyRequirement,
    RequirementError,
)


def _prebuilt_webpack_build_directory_path(
    entrypoint_providers: Sequence[WebpackEntrypointProvider & Extension],
) -> Path:
    return (
        fs.PREBUILT_ASSETS_DIRECTORY_PATH
        / "webpack"
        / f"build-{webpack_build_id(entrypoint_providers)}"
    )


async def _prebuild_webpack_assets() -> None:
    """
    Prebuild Webpack assets for inclusion in package builds.
    """
    job_context = Context()
    async with TemporaryDirectory() as project_configuration_directory_path_str:
        project = Project(
            ProjectConfiguration(
                configuration_file_path=Path(project_configuration_directory_path_str)
            )
        )
        async with App.new_temporary(project) as app, app:
            app.project.configuration.extensions.enable(Webpack)
            webpack = app.extensions[Webpack]
            app.project.configuration.extensions.enable(
                *{
                    extension_type
                    for extension_type in discover_extension_types()
                    if issubclass(extension_type, WebpackEntrypointProvider)
                }
            )
            await webpack.prebuild(job_context=job_context)


class WebpackEntrypointProvider:
    @classmethod
    def webpack_entrypoint_directory_path(cls) -> Path:
        """
        Get the path to the directory with the entrypoint assets.

        The directory must include at least a ``package.json`` and ``main.ts``.
        """
        raise NotImplementedError

    def webpack_entrypoint_cache_keys(self) -> Sequence[str]:
        """
        Get the keys that make a Webpack build for this provider unique.

        Providers that can be cached regardless may ``return ()``.
        """
        raise NotImplementedError


class PrebuiltAssetsRequirement(Requirement):
    def is_met(self) -> bool:
        return (fs.PREBUILT_ASSETS_DIRECTORY_PATH / "webpack").is_dir()

    def summary(self) -> Str:
        return (
            Str._("Pre-built Webpack front-end assets are available")
            if self.is_met()
            else Str._("Pre-built Webpack front-end assets are unavailable")
        )


class Webpack(Extension, CssProvider, Jinja2Provider, Generator):
    _npm_requirement = NpmRequirement()
    _prebuilt_assets_requirement = PrebuiltAssetsRequirement()
    _requirement = AnyRequirement(
        _npm_requirement,
        _prebuilt_assets_requirement,
    )

    @classmethod
    def name(cls) -> str:
        return "betty.extension.Webpack"

    @classmethod
    def enable_requirement(cls) -> Requirement:
        return AllRequirements(super().enable_requirement(), cls._requirement)

    def build_requirement(self) -> Requirement:
        return self._npm_requirement

    @classmethod
    def assets_directory_path(cls) -> Path:
        return Path(__file__).parent / "assets"

    @property
    def public_css_paths(self) -> list[str]:
        return [
            self.app.static_url_generator.generate("css/vendor.css"),
        ]

    def new_context_vars(self) -> dict[str, Any]:
        return {
            "webpack_js_entrypoints": set(),
        }

    @property
    def filters(self) -> dict[str, Callable[..., Any]]:
        return FILTERS

    @property
    def _project_entrypoint_providers(
        self,
    ) -> Sequence[WebpackEntrypointProvider & Extension]:
        return [
            extension
            for extension in self._app.extensions.flatten()
            if isinstance(extension, WebpackEntrypointProvider)
        ]

    async def generate(self, job_context: GenerationContext) -> None:
        build_directory_path = await self._generate_ensure_build_directory(
            job_context=job_context,
        )
        await self._copy_build_directory(
            build_directory_path, self._app.project.configuration.www_directory_path
        )

    async def prebuild(self, job_context: Context) -> None:
        async with TemporaryDirectory() as working_directory_path_str:
            build_directory_path = await self._new_builder(
                Path(working_directory_path_str),
                job_context=job_context,
            ).build()
            await self._copy_build_directory(
                build_directory_path,
                _prebuilt_webpack_build_directory_path(
                    self._project_entrypoint_providers
                ),
            )

    def _new_builder(
        self,
        working_directory_path: Path,
        *,
        job_context: Context,
    ) -> build.Builder:
        return build.Builder(
            working_directory_path,
            self._project_entrypoint_providers,
            self._app.project.configuration.debug,
            self._app.renderer,
            job_context=job_context,
            localizer=self._app.localizer,
        )

    async def _copy_build_directory(
        self,
        build_directory_path: Path,
        destination_directory_path: Path,
    ) -> None:
        await to_thread(
            copytree,
            build_directory_path,
            destination_directory_path,
            dirs_exist_ok=True,
        )

    async def _generate_ensure_build_directory(
        self,
        *,
        job_context: Context,
    ) -> Path:
        builder = self._new_builder(
            self._app.binary_file_cache.with_scope("webpack").path,
            job_context=job_context,
        )
        try:
            # (Re)build the assets if `npm` is available.
            return await builder.build()
        except NpmUnavailable:
            pass

        # Use prebuilt assets if they exist.
        prebuilt_webpack_build_directory_path = _prebuilt_webpack_build_directory_path(
            self._project_entrypoint_providers
        )
        if prebuilt_webpack_build_directory_path.exists():
            return prebuilt_webpack_build_directory_path

        raise RequirementError(self._requirement)
