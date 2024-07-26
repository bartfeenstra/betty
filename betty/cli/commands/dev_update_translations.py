from __future__ import annotations  # noqa D100

from betty.cli.commands import command
from betty.locale import translation
from betty.typing import internal


@internal
@command(
    short_help="Update all existing translations for Betty itself",
    help="Update all existing translations.\n\nThis is available only when developing Betty.",
)
async def dev_update_translations() -> None:  # noqa D103
    await translation.update_dev_translations()
