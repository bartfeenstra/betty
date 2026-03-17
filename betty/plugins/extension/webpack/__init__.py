"""
Integrate Betty with `Webpack <https://webpack.js.org/>`_.
"""

from __future__ import annotations

from asyncio import gather
from typing import TYPE_CHECKING, Self, final, override

from betty.asset import AssetDefinition
from betty.document import DocumentProvider, DocumentVars
from betty.extension import Extension, ExtensionDefinition
from betty.html.css import CssResourceDefinition
from betty.html.js import JsResourceDefinition
from betty.jinja.filter import JinjaFilterDefinition
from betty.plugins.asset.webpack import Webpack as WebpackAsset
from betty.plugins.css_resource.webpack import Webpack as WebpackCssResource
from betty.plugins.extension.webpack import build
from betty.plugins.extension.webpack.build import EntryPointProvider
from betty.plugins.extension.webpack.jobs import _GenerateAssets
from betty.plugins.jinja_filter.webpack_entry_point_js import WebpackEntryPointJs
from betty.plugins.js_resource.webpack_entry_point_loader import WebpackEntryPointLoader
from betty.project.generate import Generator
from betty.service.factory import Manufacturable
from betty.service.provider import service
from betty.service.requirement.project import require_project

if TYPE_CHECKING:
    from betty.job.scheduler import Scheduler
    from betty.project import Project


@final
@ExtensionDefinition(
    "webpack",
    label="Webpack",
    requires={
        AssetDefinition: WebpackAsset,
        CssResourceDefinition: WebpackCssResource,
        JinjaFilterDefinition: WebpackEntryPointJs,
        JsResourceDefinition: WebpackEntryPointLoader,
    },
)
class Webpack(Generator, Extension, DocumentProvider, Manufacturable):
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
    def new_document_vars(self) -> DocumentVars:
        return {
            "webpack_js_entry_points": set(),
        }

    @service
    async def builder(self) -> build.Builder:
        """
        The Webpack builder.
        """
        extensions, jinja = await gather(self._project.extensions, self._project.jinja)
        return build.Builder(
            [
                extension
                for extension in extensions
                if isinstance(extension, EntryPointProvider)
            ],
            self._project.configuration.debug,
            jinja,
            self._project.configuration.root_path,
            user=self._project.upstream.user,
        )
