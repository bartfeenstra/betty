from __future__ import annotations  # noqa D100

import asyncio
from typing import TYPE_CHECKING, final, Self

from typing_extensions import override

from betty import documentation
from betty.app.factory import AppDependentFactory
from betty.console.command import Command, CommandFunction, CommandDefinition
from betty.locale.localizable import _

if TYPE_CHECKING:
    import argparse

    from betty.app import App


@final
@CommandDefinition(
    id="docs",
    label=_("View the documentation"),
    description=_(
        "View Betty's interactive documentation. This will open your web browser."
    ),
)
class Docs(AppDependentFactory, Command):
    """
    A command to view Betty's documentation.
    """

    def __init__(self, app: App):
        self._app = app

    @override
    @classmethod
    async def new_for_app(cls, app: App) -> Self:
        return cls(app)

    @override
    async def configure(self, parser: argparse.ArgumentParser) -> CommandFunction:
        return self._command_function

    async def _command_function(self) -> None:
        server = documentation.DocumentationServer(
            self._app.binary_file_cache.path, user=self._app.user
        )
        async with server:
            await server.show()
            while True:
                await asyncio.sleep(999)
