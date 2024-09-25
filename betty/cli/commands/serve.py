from __future__ import annotations  # noqa D100

import asyncio
from typing import TYPE_CHECKING

from betty.asyncio import wait_to_thread
from betty.cli.commands import command, pass_project
from betty.typing import internal

if TYPE_CHECKING:
    from betty.project import Project


@internal
@command(help="Serve a generated site.")
@pass_project
def serve(project: Project) -> None:  # noqa D103
    wait_to_thread(_serve, project)


async def _serve(project: Project) -> None:
    from betty import serve

    async with serve.BuiltinProjectServer(project) as server:
        await server.show()
        while True:
            await asyncio.sleep(999)
