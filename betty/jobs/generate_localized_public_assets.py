"""
Jobs to generate localized public assets.
"""

from __future__ import annotations

from asyncio import gather, to_thread
from pathlib import Path
from typing import TYPE_CHECKING, final, override

from betty.jinja import CopyFunction, make_copy_function
from betty.job import Job
from betty.jobs.generate_static_public_assets import GenerateStaticPublicAssets

if TYPE_CHECKING:
    from babel import Locale

    from betty.job.scheduler import Scheduler
    from betty.project import Project


@final
class GenerateLocalizedPublicAssets(Job):
    """
    Generate a site's localized public assets.
    """

    def __init__(self, *, project: Project):
        super().__init__(
            self.id_for(),
            dependencies={GenerateStaticPublicAssets.id_for()},
            priority=True,
        )
        self._project = project

    @classmethod
    def id_for(cls) -> str:
        """
        Get the job ID.
        """
        return "generate-localized-public-assets"

    @override
    async def do(self, scheduler: Scheduler, /) -> None:
        jinja = await self._project.jinja
        copy_functions = {
            locale: make_copy_function(
                jinja,
                document=await self._project.new_document(
                    context=scheduler.context,
                    localizer=await self._project.localizers.get(locale),
                ),
                www_directory=self._project.www_directory,
                is_localized_and_multilingual=self._project.multilingual,
            )
            for locale in self._project.locales.keys()  # noqa: SIM118
        }
        await gather(*[
            self._generate(asset, copy_functions[locale], locale)
            async for asset in self._project.asset_directories.walk(
                Path("public") / "localized"
            )
            for locale in self._project.locales.keys()  # noqa: SIM118
        ])

    async def _generate(
        self, asset: Path, copy_function: CopyFunction, locale: Locale
    ) -> None:
        file_destination = self._project.localize_www_directory(
            locale
        ) / asset.relative_to(Path("public") / "localized")
        await to_thread(file_destination.parent.mkdir, exist_ok=True, parents=True)
        await copy_function(
            await self._project.asset_directories.get(asset), file_destination
        )
