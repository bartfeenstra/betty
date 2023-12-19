from pathlib import Path
from shutil import copyfile
from urllib.parse import urlparse

import aiofiles
from aiofiles.os import makedirs
from jinja2 import FileSystemLoader

from betty.app import App
from betty.path import rootname


async def generate_configuration_file(
    app: App,
    destination_file_path: Path | None = None,
    www_directory_path: str | None = None,
    https: bool | None = None,
) -> None:
    from betty.extension import Nginx

    data = {
        'server_name': urlparse(app.project.configuration.base_url).netloc,
        'www_directory_path': www_directory_path or app.extensions[Nginx].www_directory_path,
        'https': https or app.extensions[Nginx].https,
    }
    if destination_file_path is None:
        destination_file_path = app.project.configuration.output_directory_path / 'nginx' / 'nginx.conf'
    root_path = rootname(Path(__file__))
    configuration_file_template_name = '/'.join((Path(__file__).parent / 'assets' / 'nginx.conf.j2').relative_to(root_path).parts)
    template = FileSystemLoader(root_path).load(app.jinja2_environment, configuration_file_template_name, app.jinja2_environment.globals)
    await makedirs(destination_file_path.parent, exist_ok=True)
    configuration_file_contents = await template.render_async(data)
    async with aiofiles.open(destination_file_path, 'w', encoding='utf-8') as f:
        await f.write(configuration_file_contents)


async def generate_dockerfile_file(app: App, destination_file_path: Path | None = None) -> None:
    if destination_file_path is None:
        destination_file_path = app.project.configuration.output_directory_path / 'nginx' / 'docker' / 'Dockerfile'
    await makedirs(destination_file_path.parent, exist_ok=True)
    copyfile(Path(__file__).parent / 'assets' / 'docker' / 'Dockerfile', destination_file_path)
