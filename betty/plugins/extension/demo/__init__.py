"""
Provide demonstration site functionality.
"""

from __future__ import annotations

from asyncio import to_thread
from contextlib import suppress
from shutil import rmtree
from typing import TYPE_CHECKING, Self, final, override

from betty.extension import Extension, ExtensionDefinition
from betty.license import LicenseDefinition
from betty.plugins.copyright_notice.streetmix import Streetmix
from betty.plugins.extension.demo.jobs import LoadAncestry
from betty.plugins.extension.deriver import Deriver
from betty.plugins.extension.http_api_doc import HttpApiDoc
from betty.plugins.extension.maps import Maps
from betty.plugins.extension.raspberry_mint import RaspberryMint
from betty.plugins.extension.spdx import Spdx
from betty.plugins.extension.trees import Trees
from betty.plugins.extension.wiki import Wiki
from betty.plugins.license.spdx import spdx_license_id_to_license_id
from betty.plugins.link.betty_documentation import BettyDocumentation
from betty.plugins.link.betty_github import BettyGithub
from betty.project import Project, generate
from betty.project.load import Loader, load
from betty.requirement import require
from betty.service.factory import Manufacturable

if TYPE_CHECKING:
    from betty.job import Context
    from betty.job.scheduler import Scheduler


async def generate_with_cleanup(
    project: Project, *, context: Context | None = None
) -> None:
    """
    Generate a demonstration site, and clean up the project directory on any errors.
    """
    if context:
        # Add a phantom value to the progress so it can never jump to 100% before we are entirely done here.
        await context.progress.add()

    if project.www_directory.exists():
        return
    await load(project, context=context)
    with suppress(FileNotFoundError):
        await to_thread(rmtree, project.directory)
    try:
        await generate.generate(project, context=context)
    except BaseException:
        with suppress(FileNotFoundError):
            await to_thread(rmtree, project.directory)
        raise

    if context:
        await context.progress.done()


@final
@ExtensionDefinition(
    "demo",
    label="Demo",
    requires={
        BettyDocumentation,
        BettyGithub,
        Deriver,
        HttpApiDoc,
        Maps,
        RaspberryMint,
        Spdx,
        Trees,
        Wiki,
    },
)
class Demo(Loader, Manufacturable, Extension):
    """
    .. plugin:: extension:demo.
    """

    def __init__(self, *, project: Project):
        super().__init__()
        self._project = project

    @override
    @classmethod
    @require(Project)
    async def new(cls, project: Project, /) -> Self:
        return cls(project=project)

    @override
    async def load(self, scheduler: Scheduler) -> None:
        licenses = self._project.plugins[LicenseDefinition]
        await scheduler.add(
            LoadAncestry(
                ancestry=self._project.ancestry,
                factory=self._project.factory,
                streetmix_copyright_notice=await self._project.factory.new(Streetmix),
                streetmix_license=await self._project.factory.new(
                    (
                        await licenses[
                            spdx_license_id_to_license_id("AGPL-3.0-or-later")
                        ]
                    ).cls
                ),
            )
        )
