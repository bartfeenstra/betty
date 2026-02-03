from __future__ import annotations  # noqa: D100

import asyncio
from typing import TYPE_CHECKING, Self, final

from typing_extensions import override

from betty import documentation
from betty.console.command import Command, CommandDefinition, CommandFunction
from betty.locale.localizable.gettext import _
from betty.service.level import Manufacturable
from betty.service.requirement.app import require_app

if TYPE_CHECKING:
    import argparse

    from betty.app import App


@final
@CommandDefinition(
    "docs",
    label=_("View the documentation"),
    description=_(
        "View Betty's interactive documentation. This will open your web browser."
    ),
)
class Docs(Manufacturable, Command):
    """
    .. plugin:: command:docs.
    """

    def __init__(self, app: App):
        self._app = app

    @override
    @classmethod
    @require_app
    async def new(cls, *, app: App) -> Self:
        return cls(app)

    @override
    async def configure(self, parser: argparse.ArgumentParser) -> CommandFunction:
        return self._command_function

    async def _command_function(self) -> None:
        server = documentation.DocumentationServer(
            self._app.binary_file_cache.with_scope("documentation").path,
            user=self._app.user,
        )
        async with server:
            await server.show()
            while True:
                await asyncio.sleep(999)
