from __future__ import annotations

from asyncio import to_thread
from shutil import copytree
from typing import TYPE_CHECKING, final, override

from betty.job import Job

if TYPE_CHECKING:
    from pathlib import Path

    from betty.extensions.webpack.build import Builder
    from betty.job.scheduler import Context, Scheduler


@final
class _GenerateWebpackAssets(Job):
    def __init__(self, *, builder: Builder, www_directory: Path, cache_directory: Path):
        super().__init__("webpack:generate-assets", priority=True)
        self._builder = builder
        self._cache_directory = cache_directory
        self._www_directory = www_directory

    @override
    async def do(self, scheduler: Scheduler, /) -> None:
        context = scheduler.context
        build_directory = await self._generate_ensure_build_directory(context)
        await self._copy_build_directory(build_directory, self._www_directory)

    async def _copy_build_directory(
        self, build_directory: Path, destination_directory: Path
    ) -> None:
        await to_thread(
            copytree, build_directory, destination_directory, dirs_exist_ok=True
        )

    async def _generate_ensure_build_directory(self, context: Context) -> Path:
        return await self._builder.build(
            self._cache_directory,
            context=context,
        )
