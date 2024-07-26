from __future__ import annotations  # noqa D100

import click

from betty.cli.commands import command
from betty.typing import internal


@internal
@command(
    short_help="Initialize a new translation",
    help="Initialize a new translation.\n\nThis is available only when developing Betty.",
)
@click.argument("locale")
async def dev_init_translation(locale: str) -> None:  # noqa D103
    from betty.locale.translation import init_translation

    await init_translation(locale)
