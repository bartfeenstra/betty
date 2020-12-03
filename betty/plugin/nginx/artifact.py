from os import path
from shutil import copyfile

from jinja2 import FileSystemLoader, Environment

from betty.fs import makedirs


async def generate_configuration_file(destination_file_path: str, jinja2_environment: Environment, **kwargs) -> None:
    configuration_file_template_path = path.join(path.dirname(__file__), 'assets', 'nginx.conf.j2')
    template = FileSystemLoader('/').load(jinja2_environment, configuration_file_template_path, jinja2_environment.globals)
    makedirs(path.dirname(destination_file_path))
    with open(destination_file_path, 'w') as f:
        f.write(await template.render_async(kwargs))


async def generate_dockerfile_file(destination_file_path: str) -> None:
    makedirs(path.dirname(destination_file_path))
    copyfile(path.join(path.dirname(__file__), 'assets', 'docker', 'Dockerfile'), destination_file_path)
