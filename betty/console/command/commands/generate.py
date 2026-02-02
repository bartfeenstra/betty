from __future__ import annotations  # noqa: D100

from typing import TYPE_CHECKING, Self, final

from typing_extensions import override

from betty.console.command import Command, CommandDefinition, CommandFunction
from betty.console.project import add_project_argument
from betty.locale.localizable.gettext import _
from betty.project.job import ProjectContext
from betty.service.level import Manufacturable
from betty.service.requirement.app import require_app

if TYPE_CHECKING:
    import argparse

    from betty.app import App
    from betty.project import Project


@final
@CommandDefinition("generate", label=_("Generate a static site"))
class Generate(Manufacturable, Command):
    """
    .. plugin:: command:generate.
    """

    def __init__(self, app: App):
        self._app = app

    @override
    @classmethod
    @require_app
    async def new_for_services(cls, *, app: App) -> Self:
        return cls(app)

    @override
    async def configure(self, parser: argparse.ArgumentParser) -> CommandFunction:
        return await add_project_argument(parser, self._command_function, self._app)

    async def _command_function(self, project: Project) -> None:
        from betty.project import generate, load

        async with (
            project,
            project.app.user.message_progress(_("Generating site...")) as progress,
        ):
            # Add a phantom value to the progress so it can never jump to 100% before we are entirely done here.
            await progress.add()

            job_context = ProjectContext(project, progress=progress)
            await load.load(project, job_context=job_context)
            await generate.generate(project, job_context=job_context)

            await progress.done()
