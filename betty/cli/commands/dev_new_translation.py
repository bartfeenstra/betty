from __future__ import annotations  # noqa D100

import click
from betty.cli.commands import command
from betty.locale import translation
from betty.typing import internal


@internal
@command(
    short_help="Create a new translation for Betty itself",
    help="Create a new translation.\n\nThis is available only when developing Betty.",
)
@click.argument("locale")
async def dev_new_translation(locale: str) -> None:  # noqa D103
    await translation.new_dev_translation(locale)
