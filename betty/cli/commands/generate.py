from __future__ import annotations  # noqa D100

from typing import TYPE_CHECKING

from betty.cli.commands import command, pass_project
from betty.typing import internal

if TYPE_CHECKING:
    from betty.project import Project


@internal
@command(help="Generate a static site.")
@pass_project
async def generate(project: Project) -> None:  # noqa D103
    from betty.project import generate, load

    await load.load(project)
    await generate.generate(project)
