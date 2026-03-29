"""
Generate a demonstration site.
"""

from __future__ import annotations

from asyncio import to_thread
from contextlib import suppress
from shutil import rmtree
from typing import TYPE_CHECKING

from betty.load import load
from betty.project import Project, generate

if TYPE_CHECKING:
    from betty.job import Context


async def generate_with_cleanup(
    project: Project, *, context: Context | None = None
) -> None:
    """
    Generate a demonstration site, and clean up the project directory on any errors.
    """
    if context:
        # Add a phantom value to the progress so it can never jump to 100% before we are entirely done here.
        await context.progress.add()

    if project.www_directory.exists():
        return
    await load(project, context=context)
    with suppress(FileNotFoundError):
        await to_thread(rmtree, project.directory)
    try:
        await generate.generate(project, context=context)
    except BaseException:
        with suppress(FileNotFoundError):
            await to_thread(rmtree, project.directory)
        raise

    if context:
        await context.progress.done()
