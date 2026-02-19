"""
Integrate Betty with `Webpack <https://webpack.js.org/>`_.

This module is internal.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Self, final, override

from betty.document import DocumentProvider, DocumentVars
from betty.extension import Extension, ExtensionDefinition
from betty.extension.webpack import build
from betty.extension.webpack.build import EntryPointProvider
from betty.extension.webpack.jinja.filter import FILTERS
from betty.extension.webpack.jobs import _GenerateAssets
from betty.html import CssProvider, JsProvider
from betty.jinja import Filters, JinjaProvider
from betty.project import Project
from betty.project.generate import Generator
from betty.service.container import service
from betty.service.factory import Manufacturable
from betty.service.requirement.project import require_project

if TYPE_CHECKING:
    from collections.abc import Sequence

    from betty.job.scheduler import Scheduler


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
    JinjaProvider,
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
    async def generate(self, scheduler: Scheduler) -> None:

        await scheduler.add(
            _GenerateAssets(
                builder=await self.builder,
                cache_directory=self.services.app.binary_file_cache.with_scope(
                    "webpack"
                ).path,
                www_directory=self.services.www_directory,
            )
        )

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

    @service
    async def builder(self) -> build.Builder:
        """
        The Webpack builder.
        """
        return build.Builder(
            await self._project_entry_point_providers(),
            self.services.configuration.debug,
            await self.services.jinja,
            self.services.configuration.root_path,
            user=self.services.app.user,
        )
