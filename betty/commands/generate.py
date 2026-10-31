from __future__ import annotations  # noqa: D100

from typing import TYPE_CHECKING, Self, final, override

from betty import load
from betty.app import App
from betty.commands.project import add_project_argument
from betty.console import Command, CommandDefinition, CommandResult
from betty.factory import Manufacturable
from betty.job import Context
from betty.localizables.gettext import _
from betty.project import generate

if TYPE_CHECKING:
    from argparse import ArgumentParser

    from betty.console import CommandFunction
    from betty.project import Project


@final
@CommandDefinition("generate", label=_("Generate a static site"), aliases=["g"])
class Generate(Manufacturable, Command):
    """
    .. plugin:: command:generate.
    """

    def __init__(self, app: App, /):
        self._app = app

    @override
    @App.require
    @classmethod
    async def new(cls, app: App, /) -> Self:
        return cls(app)

    @override
    async def configure(self, parser: ArgumentParser, /) -> CommandFunction:
        return await add_project_argument(parser, self._command_function, self._app)

    async def _command_function(self, project: Project) -> CommandResult:
        async with (
            project,
            project.upstream.ui.progress(_("Generating site…")) as progress,
        ):
            context = Context(progress=progress)
            await load.load(project, context=context)
            await generate.generate(project, context=context)
