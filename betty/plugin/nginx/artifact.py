from os import path
from pathlib import Path
from shutil import copyfile

from jinja2 import FileSystemLoader, Environment

from betty.fs import makedirs
from betty.path import rootname


async def generate_configuration_file(destination_file_path: str, jinja2_environment: Environment, **kwargs) -> None:
    root_path = rootname(__file__)
    configuration_file_template_name = '/'.join(Path(path.relpath(path.join(path.dirname(__file__), 'assets', 'nginx.conf.j2'), root_path)).parts)
    template = FileSystemLoader(root_path).load(jinja2_environment, configuration_file_template_name, jinja2_environment.globals)
    makedirs(path.dirname(destination_file_path))
    with open(destination_file_path, 'w') as f:
        f.write(await template.render_async(kwargs))


async def generate_dockerfile_file(destination_file_path: str) -> None:
    makedirs(path.dirname(destination_file_path))
    copyfile(path.join(path.dirname(__file__), 'assets', 'docker', 'Dockerfile'), destination_file_path)
