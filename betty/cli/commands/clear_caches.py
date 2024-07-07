from __future__ import annotations  # noqa D100

import click

from betty.cli.commands import command, pass_app
from typing import TYPE_CHECKING

from betty.typing import internal

if TYPE_CHECKING:
    from betty.app import App


@internal
@click.command(help="Clear all caches.")
@pass_app
@command
async def clear_caches(app: App) -> None:  # noqa D103
    await app.cache.clear()
