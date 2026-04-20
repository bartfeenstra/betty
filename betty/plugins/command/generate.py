from __future__ import annotations  # noqa: D100

from typing import TYPE_CHECKING, Self, final, override

from betty.app import App
from betty.console.command import Command, CommandDefinition, CommandFunction
from betty.console.project import add_project_argument
from betty.factory import Manufacturable
from betty.job import Context
from betty.locale.localizable.gettext import _

if TYPE_CHECKING:
    import argparse

    from betty.project import Project


@final
@CommandDefinition("generate", label=_("Generate a static site"), aliases=["g"])
class Generate(Manufacturable, Command):
    """
    .. plugin:: command:generate.
    """

    def __init__(self, app: App):
        self._app = app

    @override
    @App.require
    @classmethod
    async def new(cls, app: App, /) -> Self:
        return cls(app)

    @override
    async def configure(self, parser: argparse.ArgumentParser) -> CommandFunction:
        return await add_project_argument(parser, self._command_function, self._app)

    async def _command_function(self, project: Project) -> None:
        from betty import load
        from betty.project import generate

        async with (
            project,
            project.upstream.user.message_progress(_("Generating site...")) as progress,
        ):
            # Add a phantom value to the progress so it can never jump to 100% before we are entirely done here.
            await progress.add()

            context = Context(progress=progress)
            await load.load(project, context=context)
            await generate.generate(project, context=context)

            await progress.done()
