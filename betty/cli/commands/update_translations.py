from __future__ import annotations  # noqa D100

import click

import betty.locale.translation
from betty.cli.commands import command
from betty.typing import internal


@internal
@click.command(
    short_help="Update all existing translations",
    help="Update all existing translations.\n\nThis is available only when developing Betty.",
)
@command
async def update_translations() -> None:  # noqa D103
    await betty.locale.translation.update_translations()
