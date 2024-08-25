"""
Build nginx and Docker artifacts, such as configuration files.
"""

import asyncio
from pathlib import Path
from shutil import copyfile
from urllib.parse import urlparse

import aiofiles
from aiofiles.os import makedirs
from jinja2 import FileSystemLoader

from betty.path import rootname
from betty.project import Project


async def generate_configuration_file(
    project: Project,
    destination_file_path: Path | None = None,
    www_directory_path: str | None = None,
    https: bool | None = None,
) -> None:
    """
    Generate an ``nginx.conf`` file to the given destination path.
    """
    from betty.extension.nginx import Nginx

    nginx = project.extensions[Nginx]
    data = {
        "server_name": urlparse(project.configuration.base_url).netloc,
        "www_directory_path": www_directory_path or nginx.www_directory_path,
        "https": https or nginx.https,
    }
    if destination_file_path is None:
        destination_file_path = (
            project.configuration.output_directory_path / "nginx" / "nginx.conf"
        )
    root_path = rootname(Path(__file__))
    configuration_file_template_name = "/".join(
        (Path(__file__).parent / "assets" / "nginx.conf.j2")
        .relative_to(root_path)
        .parts
    )
    template = FileSystemLoader(root_path).load(
        project.jinja2_environment,
        configuration_file_template_name,
        project.jinja2_environment.globals,
    )
    await makedirs(destination_file_path.parent, exist_ok=True)
    configuration_file_contents = await template.render_async(data)
    async with aiofiles.open(destination_file_path, "w", encoding="utf-8") as f:
        await f.write(configuration_file_contents)


async def generate_dockerfile_file(
    project: Project, destination_file_path: Path | None = None
) -> None:
    """
    Generate a ``Dockerfile`` to the given destination path.
    """
    if destination_file_path is None:
        destination_file_path = (
            project.configuration.output_directory_path / "nginx" / "Dockerfile"
        )
    await makedirs(destination_file_path.parent, exist_ok=True)
    await asyncio.to_thread(
        copyfile, Path(__file__).parent / "assets" / "Dockerfile", destination_file_path
    )
    await asyncio.to_thread(
        copyfile,
        Path(__file__).parent / "assets" / "content_negotiation.lua",
        destination_file_path.parent / "content_negotiation.lua",
    )
