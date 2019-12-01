from os.path import join, dirname
from typing import List, Tuple, Callable, Type, Dict, Optional

from jinja2 import Environment

from betty.jinja2 import render_file
from betty.plugin import Plugin
from betty.render import PostRenderEvent
from betty.site import Site


class Nginx(Plugin):
    def __init__(self, site: Site):
        self._site = site

    @classmethod
    def from_configuration_dict(cls, site: Site, configuration: Dict):
        return cls(site)

    def subscribes_to(self) -> List[Tuple[Type, Callable]]:
        return [
            (PostRenderEvent, lambda event: self._render_config(event.environment)),
        ]

    @property
    def resource_directory_path(self) -> Optional[str]:
        return '%s/resources' % dirname(__file__)

    def _render_config(self, environment: Environment) -> None:
        file_name = 'nginx.conf.j2'
        destination_file_path = join(
            self._site.configuration.output_directory_path, file_name)
        self._site.resources.copy2(file_name, destination_file_path)
        render_file(destination_file_path, environment)
