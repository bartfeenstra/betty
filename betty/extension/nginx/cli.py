"""
Provide Command Line Interface functionality.
"""

import asyncio

import click

from betty.cli import pass_project, command
from betty.extension.nginx import serve
from betty.project import Project


@click.command(help="Serve a generated site with nginx in a Docker container.")
@pass_project
@command
async def _serve(project: Project) -> None:
    async with serve.DockerizedNginxServer(project) as server:
        await server.show()
        while True:
            await asyncio.sleep(999)
