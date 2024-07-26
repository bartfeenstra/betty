from __future__ import annotations  # noqa D100

from typing import TYPE_CHECKING

import click
from betty.cli.commands import command, pass_project
from betty.locale import translation
from betty.typing import internal

if TYPE_CHECKING:
    from betty.project import Project


@internal
@command(short_help="Create a new translation")
@click.argument("locale")
@pass_project
async def new_translation(project: Project, locale: str) -> None:  # noqa D103
    await translation.new_project_translation(locale, project)
