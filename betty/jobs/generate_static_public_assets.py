"""
Jobs to generate static public assets.
"""

from __future__ import annotations

from asyncio import gather, to_thread
from pathlib import Path
from typing import TYPE_CHECKING, final, override

from betty.jinja import CopyFunction, make_copy_function
from betty.job import Job

if TYPE_CHECKING:
    from betty.job.scheduler import Scheduler
    from betty.project import Project


@final
class GenerateStaticPublicAssets(Job):
    """
    Generate a site's static public assets.
    """

    def __init__(self, *, project: Project):
        super().__init__(self.id_for(), priority=True)
        self._project = project

    @classmethod
    def id_for(cls) -> str:
        """
        Get the job ID.
        """
        return "generate-static-public-assets"

    @override
    async def do(self, scheduler: Scheduler, /) -> None:
        jinja = await self._project.jinja
        copy_function = make_copy_function(
            jinja,
            document=await self._project.new_document(context=scheduler.context),
            www_directory=self._project.www_directory,
            is_localized_and_multilingual=self._project.multilingual,
        )
        await gather(*[
            self._generate(asset_path, copy_function)
            async for asset_path in self._project.asset_directories.walk(
                Path("public") / "static"
            )
        ])

    async def _generate(self, asset: Path, copy_function: CopyFunction, /) -> None:
        file_destination_path = self._project.www_directory / asset.relative_to(
            Path("public") / "static"
        )
        await to_thread(file_destination_path.parent.mkdir, exist_ok=True, parents=True)
        await copy_function(
            await self._project.asset_directories.get(asset), file_destination_path
        )
