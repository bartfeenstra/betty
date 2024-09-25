from __future__ import annotations  # noqa D100

import asyncio
from typing import TYPE_CHECKING

from betty import documentation
from betty.asyncio import wait_to_thread
from betty.cli.commands import command, pass_app
from betty.typing import internal

if TYPE_CHECKING:
    from betty.app import App


@internal
@command(help="View the documentation.")
@pass_app
def docs(app: App):  # noqa D103
    wait_to_thread(_docs, app)


async def _docs(app: App):
    server = documentation.DocumentationServer(
        app.binary_file_cache.path,
        localizer=app.localizer,
    )
    async with server:
        await server.show()
        while True:
            await asyncio.sleep(999)
