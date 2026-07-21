from __future__ import annotations  # noqa: D100

import asyncio
from typing import TYPE_CHECKING, Self, final, override

from betty.app import App
from betty.console.command import Command, CommandDefinition, CommandFunction
from betty.console.project import add_project_argument
from betty.factory import Manufacturable
from betty.localizables.gettext import _

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

    def __init__(self, app: App, /):
        self._app = app

    @override
    @App.require
    @classmethod
    async def new(cls, app: App, /) -> Self:
        return cls(app)

    @override
    async def configure(self, parser: argparse.ArgumentParser) -> CommandFunction:
        localizer = await self._app.localizer
        parser.add_argument(
            "-s",
            "--server",
            dest="server_id",
            help=localizer.translate._("The web server to use."),
        )
        return await add_project_argument(parser, self._command_function, self._app)

    async def _command_function(self, project: Project, server_id: str | None) -> None:
        async with project:
            if server_id is None:
                server = await next(iter(project.servers))
            else:
                server = await project.servers[server_id]
            async with server:
                await server.show()
                await self._wait_forever()

    async def _wait_forever(self) -> None:
        while True:
            await asyncio.sleep(999)
