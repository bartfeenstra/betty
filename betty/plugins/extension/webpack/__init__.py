"""
Integrate Betty with `Webpack <https://webpack.js.org/>`_.
"""

from __future__ import annotations

from asyncio import gather
from typing import TYPE_CHECKING, Self, final, override

from betty.asset_directories.webpack import WEBPACK as WEBPACK_ASSET
from betty.css_resources.webpack import WEBPACK as WEBPACK_CSS_RESOURCE
from betty.extension import Extension, ExtensionDefinition
from betty.factory import Manufacturable
from betty.plugins.extension.webpack import build
from betty.plugins.extension.webpack.build import EntryPointProvider
from betty.plugins.extension.webpack.jobs import _GenerateAssets
from betty.plugins.jinja_filter.webpack_entry_point_js import WebpackEntryPointJs
from betty.plugins.js_resource.webpack_entry_point_loader import (
    WEBPACK_ENTRY_POINT_LOADER,
)
from betty.project import Project
from betty.project.generate import Generator
from betty.service import ServiceProvider
from betty.service.simple import service

if TYPE_CHECKING:
    from betty.job.scheduler import Scheduler


@final
@ExtensionDefinition(
    "webpack",
    label="Webpack",
    requires={
        Project.asset_directories.require(WEBPACK_ASSET),
        Project.css_resources.require(WEBPACK_CSS_RESOURCE),
        Project.jinja_filters.require(WebpackEntryPointJs),
        Project.js_resources.require(WEBPACK_ENTRY_POINT_LOADER),
    },
)
class Webpack(Generator, Extension, ServiceProvider, Manufacturable):
    """
    .. plugin:: extension:webpack.
    """

    def __init__(self, *, project: Project):
        super().__init__(services=project)
        self._project = project

    @override
    @Project.require
    @classmethod
    async def new(cls, project: Project, /) -> Self:
        return cls(project=project)

    @override
    async def generate(self, scheduler: Scheduler) -> None:
        await scheduler.add(
            _GenerateAssets(
                builder=await self.builder,
                cache_directory=self._project.binary_file_cache.with_scope(
                    "webpack"
                ).directory,
                www_directory=self._project.www_directory,
            )
        )

    @service
    async def builder(self) -> build.Builder:
        """
        The Webpack builder.
        """
        return build.Builder(
            [
                extension
                for extension in await gather(*self._project.extensions)
                if isinstance(extension, EntryPointProvider)
            ],
            self._project.debug,
            await self._project.jinja,
            self._project.root_path,
            user=self._project.upstream.user,
        )
