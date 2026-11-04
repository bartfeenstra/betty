from __future__ import annotations

from asyncio import to_thread
from shutil import copytree
from typing import TYPE_CHECKING, final, override

from betty.job import Job
from betty.jobs.generate_www_directory import GenerateWwwDirectory

if TYPE_CHECKING:
    from pathlib import Path

    from betty.job.scheduler import Scheduler
    from betty.service_providers.webpack.build import Builder


@final
class _GenerateWebpackAssets(Job):
    def __init__(self, *, builder: Builder, www_directory: Path, cache_directory: Path):
        super().__init__(
            "webpack:generate-assets",
            dependencies=[GenerateWwwDirectory.id_for],
            priority=True,
        )
        self._builder = builder
        self._cache_directory = cache_directory
        self._www_directory = www_directory

    @override
    async def do(self, scheduler: Scheduler, /) -> None:
        context = scheduler.context
        build_directory = await self._builder.build(
            self._cache_directory, context=context
        )
        await to_thread(
            copytree, build_directory, self._www_directory, dirs_exist_ok=True
        )
