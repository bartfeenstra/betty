"""
Provide Command Line Interface functionality.
"""

import asyncio

import click

from betty.app import App
from betty.cli import app_command
from betty.extension.nginx import serve


@click.command(help="Serve a generated site with nginx in a Docker container.")
@app_command
async def _serve(app: App) -> None:
    async with serve.DockerizedNginxServer(app) as server:
        await server.show()
        while True:
            await asyncio.sleep(999)
