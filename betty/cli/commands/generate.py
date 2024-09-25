from __future__ import annotations  # noqa D100

from typing import TYPE_CHECKING

from betty.asyncio import wait_to_thread
from betty.cli.commands import command, pass_project
from betty.typing import internal

if TYPE_CHECKING:
    from betty.project import Project


@internal
@command(help="Generate a static site.")
@pass_project
def generate(project: Project) -> None:  # noqa D103
    wait_to_thread(_generate, project)


async def _generate(project: Project) -> None:
    from betty.project import generate, load

    await load.load(project)
    await generate.generate(project)
