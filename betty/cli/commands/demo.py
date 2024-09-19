from __future__ import annotations  # noqa D100

import asyncio
from typing import TYPE_CHECKING

from betty.cli.commands import command, pass_app
from betty.typing import internal

if TYPE_CHECKING:
    from betty.app import App


@internal
@command(help="Explore a demonstration site.")
@pass_app
async def demo(app: App) -> None:  # noqa D103
    from betty.project.extension.demo import DemoServer

    async with DemoServer(app=app) as server:
        await server.show()
        while True:
            await asyncio.sleep(999)
