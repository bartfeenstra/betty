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
from betty.job import Job
from betty.locale.localizable import StaticTranslations
from betty.os import copy_tree
from betty.plugin import ShorthandPluginBase
from betty.project import ProjectContext
from betty.project.extension import Extension
from betty.project.extension.webpack import build
from betty.project.extension.webpack.build import EntryPointProvider
from betty.project.extension.webpack.jinja2.filter import FILTERS
from betty.project.generate import Generator
from betty.requirement import AllRequirements, Requirement, RequirementError
from betty.typing import internal

if TYPE_CHECKING:
    from collections.abc import Sequence

    from betty.job.scheduler import Scheduler
    from betty.user import User


class _GenerateAssets(Job[ProjectContext]):
    def __init__(self):
        super().__init__("webpack:generate-assets", priority=True)

    @override
    async def do(self, scheduler: Scheduler[ProjectContext], /) -> None:
        context = scheduler.context
        project = context.project
        extensions = await project.extensions
        webpack = extensions[Webpack]
        build_directory_path = await webpack._generate_ensure_build_directory(
            job_context=context
        )
        context._webpack_build_directory_path = build_directory_path  # type: ignore[attr-defined]
        await webpack._copy_build_directory(
            build_directory_path, project.configuration.www_directory_path
        )


@internal
@final
class Webpack(
    ShorthandPluginBase, Generator, Extension, CssProvider, JsProvider, Jinja2Provider
):
    """
    Integrate Betty with `Webpack <https://webpack.js.org/>`_.
    """

    _plugin_id = "webpack"
    _plugin_label = StaticTranslations("Webpack")
    _requirement: ClassVar[Requirement | None] = None

    @override
    async def generate(self, scheduler: Scheduler[ProjectContext]) -> None:
        await scheduler.add(_GenerateAssets())

    @override
    @classmethod
    async def requirement(cls, *, user: User) -> Requirement:
        if cls._requirement is None:
            cls._requirement = AllRequirements(
                await super().requirement(user=user),
                await NpmRequirement.new(user=user),
            )
        return cls._requirement

    @override
    @classmethod
    def assets_directory_path(cls) -> Path:
        return Path(__file__).parent / "assets"

    @override
    async def get_public_css_paths(self) -> Sequence[str]:
        return (
            "betty-static:///css/webpack/webpack-vendor.css",
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
        job_context: ProjectContext,
    ) -> build.Builder:
        return build.Builder(
            working_directory_path,
            await self._project_entry_point_providers(),
            self._project.configuration.debug,
            await self._project.renderer,
            self._project.configuration.root_path,
            job_context=job_context,
            user=self._project.app.user,
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
        job_context: ProjectContext,
    ) -> Path:
        builder = await self._new_builder(
            self._project.app.binary_file_cache.with_scope("webpack").path,
            job_context=job_context,
        )
        try:
            # (Re)build the assets if `npm` is available.
            return await builder.build()
        except NpmUnavailable:
            raise RequirementError(
                await self.requirement(user=self._project.app.user)
            ) from None
