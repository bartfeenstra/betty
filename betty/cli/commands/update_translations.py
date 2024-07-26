from __future__ import annotations  # noqa D100

from pathlib import Path
from typing import TYPE_CHECKING

import click
from betty.cli.commands import command, pass_project
from betty.locale import translation
from betty.typing import internal

if TYPE_CHECKING:
    from betty.project import Project


@internal
@command(short_help="Update all existing translations")
@click.argument("source", nargs=-1, type=Path)
@pass_project
async def update_translations(project: Project, source: tuple[Path]) -> None:  # noqa D103
    await translation.update_project_translations(project, set(source))
