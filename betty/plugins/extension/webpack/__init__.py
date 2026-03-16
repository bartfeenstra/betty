"""
Integrate Betty with `Webpack <https://webpack.js.org/>`_.

This module is internal.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from betty.asset import AssetDefinition
from betty.document import DocumentProvider, DocumentVars
from betty.extension import Extension, ExtensionDefinition
from betty.html import CssProvider
from betty.html.js import JsResourceDefinition
from betty.jinja import Filters, JinjaProvider
from betty.plugins.asset.webpack import Webpack as WebpackAsset
from betty.plugins.extension.webpack import build
from betty.plugins.extension.webpack.build import EntryPointProvider
from betty.plugins.extension.webpack.jinja.filter import FILTERS
from betty.plugins.extension.webpack.jobs import _GenerateAssets
from betty.plugins.js_resource.webpack_entry_point_loader import WebpackEntryPointLoader
from betty.project.generate import Generator
from betty.service.factory import Manufacturable
from betty.service.provider import service
from betty.service.requirement.project import require_project

if TYPE_CHECKING:
    from collections.abc import Sequence

    from betty.job.scheduler import Scheduler
    from betty.project import Project


@final
@ExtensionDefinition(
    "webpack",
    label="Webpack",
    requires={
        AssetDefinition: WebpackAsset,
        JsResourceDefinition: WebpackEntryPointLoader,
    },
)
class Webpack(
    Generator,
    Extension,
    CssProvider,
    JinjaProvider,
    DocumentProvider,
    Manufacturable,
):
    """
    .. plugin:: extension:webpack.
    """

    def __init__(self, *, project: Project):
        super().__init__()
        self._project = project

    @override
    @classmethod
    @require_project
    async def new(cls, project: Project, /) -> Self:
        return cls(project=project)

    @override
    async def generate(self, scheduler: Scheduler) -> None:

        await scheduler.add(
            _GenerateAssets(
                builder=await self.builder,
                cache_directory=self._project.upstream.binary_file_cache.with_scope(
                    "webpack"
                ).path,
                www_directory=self._project.www_directory,
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
        return [
            extension
            for extension in await self._project.extensions
            if isinstance(extension, EntryPointProvider)
        ]

    @service
    async def builder(self) -> build.Builder:
        """
        The Webpack builder.
        """
        return build.Builder(
            await self._project_entry_point_providers(),
            self._project.configuration.debug,
            await self._project.jinja,
            self._project.configuration.root_path,
            user=self._project.upstream.user,
        )
