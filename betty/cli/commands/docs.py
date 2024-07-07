from __future__ import annotations  # noqa D100

import asyncio

import click

from betty import documentation
from betty.cli.commands import command, pass_app
from typing import TYPE_CHECKING

from betty.typing import internal

if TYPE_CHECKING:
    from betty.app import App


@internal
@click.command(help="View the documentation.")
@pass_app
@command
async def docs(app: App):  # noqa D103
    server = documentation.DocumentationServer(
        app.binary_file_cache.path,
        localizer=app.localizer,
    )
    async with server:
        await server.show()
        while True:
            await asyncio.sleep(999)
