"""
Provide Command Line Interface functionality.
"""

import asyncio

from betty.cli.commands import command, pass_project
from betty.extension.nginx import serve
from betty.project import Project
from betty.typing import internal


@internal
@command(help="Serve a generated site with nginx in a Docker container.")
@pass_project
async def serve_nginx_docker(project: Project) -> None:
    async with serve.DockerizedNginxServer(project) as server:
        await server.show()
        while True:
            await asyncio.sleep(999)
