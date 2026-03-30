"""
Jobs for the Webpack extension.
"""

from __future__ import annotations

from asyncio import to_thread
from shutil import copytree
from typing import TYPE_CHECKING, override

from betty.job import Context, Job

if TYPE_CHECKING:
    from pathlib import Path

    from betty.job.scheduler import Scheduler
    from betty.webpack import Builder


class _GenerateAssets(Job):
    def __init__(self, *, builder: Builder, www_directory: Path, cache_directory: Path):
        super().__init__("webpack:generate-assets", priority=True)
        self._builder = builder
        self._cache_directory = cache_directory
        self._www_directory = www_directory

    @override
    async def do(self, scheduler: Scheduler, /) -> None:
        context = scheduler.context
        build_directory_path = await self._generate_ensure_build_directory(context)
        context._webpack_build_directory_path = build_directory_path  # ty:ignore[unresolved-attribute]
        await self._copy_build_directory(build_directory_path, self._www_directory)

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
