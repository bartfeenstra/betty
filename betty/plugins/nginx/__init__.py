import os
from shutil import copyfile
from typing import List, Tuple, Callable, Type, Dict, Optional

from voluptuous import Schema, Required, Any

from betty.config import validate_configuration
from betty.event import Event
from betty.fs import makedirs
from betty.jinja2 import render_file, create_environment
from betty.plugin import Plugin
from betty.render import PostRenderEvent
from betty.site import Site

DOCKER_PATH = os.path.join(os.path.dirname(__file__), 'resources', 'docker')

ConfigurationSchema = Schema({
    Required('www_directory_path', default=None): Any(None, str),
    Required('https', default=None): Any(None, bool),
})


class Nginx(Plugin):
    def __init__(self, site: Site, www_directory_path: Optional[str] = None, https: Optional[bool] = None):
        self._https = https
        self._www_directory_path = www_directory_path
        self._site = site

    @classmethod
    def from_configuration_dict(cls, site: Site, configuration: Dict):
        configuration = validate_configuration(ConfigurationSchema, configuration)
        return cls(site, configuration['www_directory_path'], configuration['https'])

    def subscribes_to(self) -> List[Tuple[Type[Event], Callable]]:
        return [
            (PostRenderEvent, lambda event: self._render_config()),
        ]

    @property
    def resource_directory_path(self) -> Optional[str]:
        return '%s/resources' % os.path.dirname(__file__)

    @property
    def https(self) -> bool:
        if self._https is None:
            return self._site.configuration.base_url.startswith('https')
        return self._https

    @property
    def www_directory_path(self) -> str:
        if self._www_directory_path is None:
            return self._site.configuration.www_directory_path
        return self._www_directory_path

    def _render_config(self) -> None:
        output_directory_path = os.path.join(self._site.configuration.output_directory_path, 'nginx')
        makedirs(output_directory_path)

        # Render the ngnix configuration.
        file_name = 'nginx.conf.j2'
        destination_file_path = os.path.join(output_directory_path, file_name)
        self._site.resources.copy2(file_name, destination_file_path)

        # Render the Dockerfile.
        render_file(destination_file_path, create_environment(self._site))
        copyfile(os.path.join(DOCKER_PATH, 'Dockerfile'), os.path.join(output_directory_path, 'Dockerfile'))
