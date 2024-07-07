from __future__ import annotations  # noqa D100

import asyncio

import click

from betty.cli.commands import command, pass_app
from typing import TYPE_CHECKING

from betty.typing import internal

if TYPE_CHECKING:
    from betty.app import App


@internal
@click.command(help="Explore a demonstration site.")
@pass_app
@command
async def demo(app: App) -> None:  # noqa D103
    from betty.extension.demo import DemoServer

    async with DemoServer(app=app) as server:
        await server.show()
        while True:
            await asyncio.sleep(999)
