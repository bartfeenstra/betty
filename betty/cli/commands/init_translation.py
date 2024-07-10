from __future__ import annotations  # noqa D100

import click

from betty.cli.commands import command
from betty.typing import internal


@internal
@click.command(
    short_help="Initialize a new translation",
    help="Initialize a new translation.\n\nThis is available only when developing Betty.",
)
@click.argument("locale")
@command
async def init_translation(locale: str) -> None:  # noqa D103
    from betty.locale import init_translation

    await init_translation(locale)
