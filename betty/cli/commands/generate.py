from __future__ import annotations  # noqa D100

import click

from betty.cli.commands import command, pass_project
from typing import TYPE_CHECKING

from betty.typing import internal

if TYPE_CHECKING:
    from betty.project import Project


@internal
@click.command(help="Generate a static site.")
@pass_project
@command
async def generate(project: Project) -> None:  # noqa D103
    from betty import generate, load

    await load.load(project)
    await generate.generate(project)
