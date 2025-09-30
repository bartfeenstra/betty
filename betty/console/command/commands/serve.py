from __future__ import annotations  # noqa D100

import asyncio
from typing import TYPE_CHECKING, final, Self

from typing_extensions import override

from betty.app.factory import AppDependentFactory
from betty.console.command import Command, CommandFunction, CommandDefinition
from betty.console.project import add_project_argument
from betty.locale.localizable import _

if TYPE_CHECKING:
    import argparse

    from betty.app import App
    from betty.project import Project


@final
@CommandDefinition(
    id="serve",
    label=_("Serve a generated site"),
    description=_("This will open your web browser."),
)
class Serve(AppDependentFactory, Command):
    """
    A command to serve a generated site.
    """

    def __init__(self, app: App):
        self._app = app

    @override
    @classmethod
    async def new_for_app(cls, app: App) -> Self:
        return cls(app)

    @override
    async def configure(self, parser: argparse.ArgumentParser) -> CommandFunction:
        return await add_project_argument(parser, self._command_function, self._app)

    async def _command_function(self, project: Project) -> None:
        from betty import serve

        async with (
            project,
            await serve.BuiltinProjectServer.new_for_project(project) as server,
        ):
            await server.show()
            while True:
                await asyncio.sleep(999)
