"""
Provide demonstration site functionality.
"""

from __future__ import annotations

from asyncio import to_thread
from contextlib import suppress
from pathlib import Path
from shutil import rmtree
from typing import TYPE_CHECKING, final

from typing_extensions import override

from betty.html import NavigationLink, NavigationLinkProvider
from betty.locale.localizable import Plain, _
from betty.project import ProjectContext, generate
from betty.project.extension import Extension, ExtensionDefinition
from betty.project.extension.demo.jobs import LoadAncestry
from betty.project.extension.deriver import Deriver
from betty.project.extension.http_api_doc import HttpApiDoc
from betty.project.extension.maps import Maps
from betty.project.extension.raspberry_mint import RaspberryMint
from betty.project.extension.trees import Trees
from betty.project.extension.wiki import Wiki
from betty.project.load import Loader, load
from betty.typing import internal

if TYPE_CHECKING:
    from collections.abc import Sequence

    from betty.job.scheduler import Scheduler
    from betty.project import Project


@internal
async def generate_with_cleanup(
    project: Project, *, job_context: ProjectContext | None = None
) -> None:
    """
    Generate a demonstration site, and clean up the project directory on any errors.
    """
    if job_context:
        # Add a phantom value to the progress so it can never jump to 100% before we are entirely done here.
        await job_context.progress.add()

    if project.configuration.www_directory_path.exists():
        return
    await load(project, job_context=job_context)
    with suppress(FileNotFoundError):
        await to_thread(rmtree, project.configuration.project_directory_path)
    try:
        await generate.generate(project, job_context=job_context)
    except BaseException:
        with suppress(FileNotFoundError):
            await to_thread(rmtree, project.configuration.project_directory_path)
        raise

    if job_context:
        await job_context.progress.done()


@final
@ExtensionDefinition(
    id="demo",
    label=Plain("Demo"),
    depends_on={
        Deriver,
        HttpApiDoc,
        Maps,
        RaspberryMint,
        Trees,
        Wiki,
    },
    assets_directory_path=Path(__file__).parent / "assets",
)
class Demo(NavigationLinkProvider, Loader, Extension):
    """
    Provide demonstration site functionality.
    """

    @override
    async def load(self, scheduler: Scheduler[ProjectContext]) -> None:
        await scheduler.add(LoadAncestry())

    @override
    def secondary_navigation_links(self) -> Sequence[NavigationLink]:
        return [
            NavigationLink(
                "https://github.com/bartfeenstra/betty", _("Find Betty on GitHub")
            ),
            NavigationLink(
                "https://betty.readthedocs.io/", _("Read the Betty documentation")
            ),
        ]
