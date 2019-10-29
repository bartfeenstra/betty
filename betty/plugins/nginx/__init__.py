from os.path import join, dirname
from typing import List, Tuple, Callable, Type, Dict, Optional

from jinja2 import Environment
from voluptuous import Schema, Required

from betty.config import validate_configuration
from betty.jinja2 import render_file
from betty.plugin import Plugin
from betty.render import PostRenderEvent
from betty.site import Site


ConfigurationSchema = Schema({
    Required('content_negotiation', default=False): bool,
})


class Nginx(Plugin):
    def __init__(self, site: Site, content_negotiation: bool = False):
        self._site = site
        self._content_negotiation = content_negotiation

    @classmethod
    def from_configuration_dict(cls, site: Site, configuration: Dict):
        configuration = validate_configuration(ConfigurationSchema, configuration)
        return cls(site, configuration['content_negotiation'])

    def subscribes_to(self) -> List[Tuple[Type, Callable]]:
        return [
            (PostRenderEvent, lambda event: self._render_config(event.environment)),
        ]

    @property
    def resource_directory_path(self) -> Optional[str]:
        return '%s/resources' % dirname(__file__)

    @property
    def content_negotiation(self) -> bool:
        return self._content_negotiation

    def _render_config(self, environment: Environment) -> None:
        file_name = 'nginx.conf.j2'
        destination_file_path = join(
            self._site.configuration.output_directory_path, file_name)
        self._site.resources.copy2(file_name, destination_file_path)
        render_file(destination_file_path, environment)
