from pathlib import Path
from shutil import copyfile
from typing import Optional
from urllib.parse import urlparse

import aiofiles
from jinja2 import FileSystemLoader

from betty.app import App
from betty.path import rootname


async def generate_configuration_file(app: App, destination_file_path: Optional[str] = None, www_directory_path: Optional[str] = None, https: Optional[bool] = None) -> None:
    from betty.extension.nginx import Nginx

    kwargs = {
        'server_name': urlparse(app.configuration.base_url).netloc,
        'www_directory_path': app.extensions[Nginx].www_directory_path if www_directory_path is None else www_directory_path,
        'https': app.extensions[Nginx].https if https is None else https,
    }
    if destination_file_path is None:
        destination_file_path = app.configuration.output_directory_path / 'nginx' / 'nginx.conf'
    root_path = rootname(__file__)
    configuration_file_template_name = '/'.join((Path(__file__).parent / 'assets' / 'nginx.conf.j2').relative_to(root_path).parts)
    template = FileSystemLoader(root_path).load(app.jinja2_environment, configuration_file_template_name, app.jinja2_environment.globals)
    destination_file_path.parent.mkdir(exist_ok=True, parents=True)
    async with aiofiles.open(destination_file_path, 'w', encoding='utf-8') as f:
        await f.write(template.render(kwargs))


async def generate_dockerfile_file(app: App, destination_file_path: Optional[str] = None) -> None:
    if destination_file_path is None:
        destination_file_path = app.configuration.output_directory_path / 'nginx' / 'docker' / 'Dockerfile'
    destination_file_path.parent.mkdir(exist_ok=True, parents=True)
    copyfile(Path(__file__).parent / 'assets' / 'docker' / 'Dockerfile', destination_file_path)
