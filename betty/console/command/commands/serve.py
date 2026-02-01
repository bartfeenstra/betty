from __future__ import annotations  # noqa: D100

import asyncio
from typing import TYPE_CHECKING, Self, final

from typing_extensions import override

from betty.console.command import Command, CommandDefinition, CommandFunction
from betty.console.project import add_project_argument
from betty.locale.localizable.gettext import _
from betty.service.level.factory import ServiceLevelDependentSelfFactory
from betty.service.requirement.app import require_app

if TYPE_CHECKING:
    import argparse

    from betty.app import App
    from betty.project import Project


@final
@CommandDefinition(
    "serve",
    label=_("Serve a generated site"),
    description=_("This will open your web browser."),
)
class Serve(ServiceLevelDependentSelfFactory, Command):
    """
    .. plugin:: command:serve.
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
        from betty import serve

        async with (
            project,
            await serve.BuiltinProjectServer.new_for_services(
                services=project
            ) as server,
        ):
            await server.show()
            while True:
                await asyncio.sleep(999)
