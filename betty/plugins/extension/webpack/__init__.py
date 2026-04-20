"""
Integrate Betty with `Webpack <https://webpack.js.org/>`_.
"""

from __future__ import annotations

from asyncio import gather
from typing import TYPE_CHECKING, Self, final, override

from betty import webpack
from betty.extension import Extension, ExtensionDefinition
from betty.factory import Manufacturable
from betty.plugins.asset.webpack import WEBPACK as WEBPACK_ASSET
from betty.plugins.css_resource.webpack import WEBPACK as WEBPACK_CSS_RESOURCE
from betty.plugins.extension.webpack.jobs import _GenerateAssets
from betty.plugins.jinja_filter.webpack_entry_point_js import WebpackEntryPointJs
from betty.plugins.js_resource.webpack_entry_point_loader import (
    WEBPACK_ENTRY_POINT_LOADER,
)
from betty.project import Project
from betty.project.generate import Generator
from betty.service.plugin import PluginServiceProvider
from betty.service.plugin.instance import ServicePluginInstance as ServicePluginInstance
from betty.service.plugin.instance.collection.keyed import PluginInstancesService
from betty.service.simple import service
from betty.webpack import WebpackEntryPointDefinition

if TYPE_CHECKING:
    from betty.job.scheduler import Scheduler
    from betty.service.plugin.instance import ServicePluginInstances


@final
@ExtensionDefinition(
    "webpack",
    label="Webpack",
    requires={
        Project.assets.require(WEBPACK_ASSET),
        Project.css_resources.require(WEBPACK_CSS_RESOURCE),
        Project.jinja_filters.require(WebpackEntryPointJs),
        Project.js_resources.require(WEBPACK_ENTRY_POINT_LOADER),
    },
)
class Webpack(Generator, Extension, PluginServiceProvider[Project], Manufacturable):
    """
    .. plugin:: extension:webpack.
    """

    entry_points = PluginInstancesService(WebpackEntryPointDefinition)

    def __init__(
        self,
        *,
        project: Project,
        entry_points: ServicePluginInstances[WebpackEntryPointDefinition] = (),
    ):
        super().__init__(services=project)
        cls = type(self)
        cls.entry_points.add_init_plugins(self, *entry_points)

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
                cache_directory=self.services.upstream.binary_file_cache.with_scope(
                    "webpack"
                ).path,
                www_directory=self.services.www_directory,
            )
        )

    @service
    async def builder(self) -> webpack.Builder:
        """
        The Webpack builder.
        """
        return webpack.Builder(
            await gather(*self.entry_points),
            self.services.debug,
            await self.services.jinja,
            self.services.root_path,
            user=self.services.upstream.user,
        )
