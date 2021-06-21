from pathlib import Path
from shutil import copyfile

from jinja2 import FileSystemLoader, Environment

from betty.path import rootname


async def generate_configuration_file(destination_file_path: Path, jinja2_environment: Environment, **kwargs) -> None:
    root_path = rootname(__file__)
    configuration_file_template_name = '/'.join((Path(__file__).parent / 'assets' / 'nginx.conf.j2').relative_to(root_path).parts)
    template = FileSystemLoader(root_path).load(jinja2_environment, configuration_file_template_name, jinja2_environment.globals)
    destination_file_path.parent.mkdir(exist_ok=True, parents=True)
    with open(destination_file_path, 'w', encoding='utf-8') as f:
        f.write(template.render(kwargs))


async def generate_dockerfile_file(destination_file_path: Path) -> None:
    destination_file_path.parent.mkdir(exist_ok=True, parents=True)
    copyfile(Path(__file__).parent / 'assets' / 'docker' / 'Dockerfile', destination_file_path)
