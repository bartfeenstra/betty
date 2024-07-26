from __future__ import annotations  # noqa D100

import asyncio
from typing import TYPE_CHECKING

from betty.cli.commands import command, pass_project
from betty.typing import internal

if TYPE_CHECKING:
    from betty.project import Project


@internal
@command(help="Serve a generated site.")
@pass_project
async def serve(project: Project) -> None:  # noqa D103
    from betty import serve

    async with serve.BuiltinProjectServer(project) as server:
        await server.show()
        while True:
            await asyncio.sleep(999)
