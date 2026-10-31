"""
Betty's primary application console.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from betty import console
from betty.app import App


async def run(app: App, *args: str, name: str | None = None) -> None:
    """
    Launch the console.
    """
    commands = await asyncio.gather(*[
        app.factory.new(command.cls)
        async for command in app.plugins[console.CommandDefinition]
    ])
    await console.run(commands, args, name=name, ui=app.ui)


def main() -> None:
    """
    Launch the console.
    """
    asyncio.run(_main())


async def _main() -> None:
    async with App.new_from_environment() as app:
        await run(app, *sys.argv[1:], name=Path(sys.argv[0]).name)
