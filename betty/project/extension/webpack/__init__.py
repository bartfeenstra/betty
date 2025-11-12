"""
Integrate Betty with `Webpack <https://webpack.js.org/>`_.

This module is internal.
"""

from __future__ import annotations

from asyncio import to_thread
from pathlib import Path
from shutil import copytree
from typing import TYPE_CHECKING, ClassVar, final

from typing_extensions import override

from betty._npm import NpmRequirement, NpmUnavailable
from betty.html import CssProvider, JsProvider
from betty.jinja2 import Filters, Jinja2Provider
from betty.job import Job
from betty.locale.localizable import Plain
from betty.project import ProjectContext
from betty.project.extension import Extension, ExtensionDefinition
from betty.project.extension.webpack import build
from betty.project.extension.webpack.build import EntryPointProvider
from betty.project.extension.webpack.jinja2.filter import FILTERS
from betty.project.generate import Generator
from betty.requirement import AllRequirements, Requirement, RequirementError
from betty.resource import ContextProvider, ContextVars
from betty.typing import internal

if TYPE_CHECKING:
    from collections.abc import Sequence

    from betty.app import App
    from betty.job.scheduler import Scheduler


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
@ExtensionDefinition(
    id="webpack",
    label=Plain("Webpack"),
    assets_directory_path=Path(__file__).parent / "assets",
)
class Webpack(
    Generator, Extension, CssProvider, JsProvider, Jinja2Provider, ContextProvider
):
    """
    Integrate Betty with `Webpack <https://webpack.js.org/>`_.
    """

    _requirement: ClassVar[Requirement | None] = None

    @override
    async def generate(self, scheduler: Scheduler[ProjectContext]) -> None:
        await scheduler.add(_GenerateAssets())

    @override
    @classmethod
    async def requirement(cls, *, app: App) -> Requirement:
        if cls._requirement is None:
            cls._requirement = AllRequirements(
                await super().requirement(app=app),
                await NpmRequirement.new(user=app.user),
            )
        return cls._requirement

    @override
    async def get_public_css_paths(self) -> Sequence[str]:
        return (
            "betty-static:///css/webpack/webpack-vendor.css",
            *(
                f"betty-static:///css/webpack/{entry_point.plugin.id}.css"
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
    def new_resource_context(self) -> ContextVars:
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
        self, build_directory_path: Path, destination_directory_path: Path
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
                await self.requirement(app=self._project.app)
            ) from None
