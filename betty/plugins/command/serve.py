from __future__ import annotations  # noqa: D100

import asyncio
from typing import TYPE_CHECKING, Self, final, override

from betty.app import App
from betty.console.command import Command, CommandDefinition, CommandFunction
from betty.console.project import add_project_argument
from betty.locale.localizable.gettext import _
from betty.requirement import require
from betty.service.factory import Manufacturable

if TYPE_CHECKING:
    import argparse

    from betty.project import Project


@final
@CommandDefinition(
    "serve",
    label=_("Serve a generated site"),
    description=_("This will open your web browser."),
)
class Serve(Manufacturable, Command):
    """
    .. plugin:: command:serve.
    """

    def __init__(self, app: App):
        self._app = app

    @override
    @classmethod
    @require(App)
    async def new(cls, app: App, /) -> Self:
        return cls(app)

    @override
    async def configure(self, parser: argparse.ArgumentParser) -> CommandFunction:
        return await add_project_argument(parser, self._command_function, self._app)

    async def _command_function(self, project: Project) -> None:
        from betty import serve

        async with (
            project,
            await serve.BuiltinProjectServer.new(project) as server,
        ):
            await server.show()
            while True:
                await asyncio.sleep(999)
