"""
Integrate Betty with `Webpack <https://webpack.js.org/>`_.

This module is internal.
"""

from __future__ import annotations

from asyncio import to_thread
from pathlib import Path
from shutil import copytree
from typing import TYPE_CHECKING, Self, final

from typing_extensions import override

from betty.document import DocumentProvider, DocumentVars
from betty.extension import Extension, ExtensionDefinition
from betty.extension.webpack import build
from betty.extension.webpack.build import EntryPointProvider
from betty.extension.webpack.jinja2.filter import FILTERS
from betty.html import CssProvider, JsProvider
from betty.jinja2 import Filters, Jinja2Provider
from betty.project import Project
from betty.project.generate import Generator
from betty.service.factory import Manufacturable
from betty.service.requirement.project import require_project

if TYPE_CHECKING:
    from collections.abc import Sequence

    from betty.job.scheduler import Scheduler
    from betty.project.job import ProjectContext


@final
@ExtensionDefinition(
    "webpack",
    label="Webpack",
    assets_directory=Path(__file__).parent / "assets",
)
class Webpack(
    Generator,
    Extension[Project],
    CssProvider,
    JsProvider,
    Jinja2Provider,
    DocumentProvider,
    Manufacturable,
):
    """
    .. plugin:: extension:webpack.
    """

    @override
    @classmethod
    @require_project
    async def new(cls, project: Project, /) -> Self:
        return cls(services=project)

    @override
    async def generate(self, scheduler: Scheduler[ProjectContext]) -> None:
        from betty.extension.webpack.jobs import _GenerateAssets

        await scheduler.add(_GenerateAssets())

    @override
    async def get_public_css_paths(self) -> Sequence[str]:
        return (
            "betty-static:///css/webpack/webpack-vendor.css",
            *(
                f"betty-static:///css/webpack/{entry_point.plugin().id}.css"
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
    def new_document_vars(self) -> DocumentVars:
        return {
            "webpack_js_entry_points": set(),
        }

    @override
    @property
    def filters(self) -> Filters:
        return FILTERS

    async def _project_entry_point_providers(
        self,
    ) -> Sequence[EntryPointProvider]:
        extensions = await self.services.extensions
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
            self.services.configuration.debug,
            await self.services.jinja,
            self.services.configuration.root_path,
            job_context=job_context,
            user=self.services.app.user,
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
            self.services.app.binary_file_cache.with_scope("webpack").path,
            job_context=job_context,
        )
        return await builder.build()
