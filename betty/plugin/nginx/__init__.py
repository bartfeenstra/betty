import os
from shutil import copyfile
from typing import Optional, Any

from voluptuous import Schema, Required, Maybe

from betty.fs import makedirs
from betty.generate import PostGenerator
from betty.plugin import Plugin, NO_CONFIGURATION
from betty.site import Site

DOCKER_PATH = os.path.join(os.path.dirname(__file__), 'assets', 'docker')


class Nginx(Plugin, PostGenerator):
    configuration_schema: Schema = Schema({
        Required('www_directory_path', default=None): Maybe(str),
        Required('https', default=None): Maybe(bool),
    })

    def __init__(self, site: Site, www_directory_path: Optional[str] = None, https: Optional[bool] = None):
        self._https = https
        self._www_directory_path = www_directory_path
        self._site = site

    @classmethod
    def for_site(cls, site: Site, configuration: Any = NO_CONFIGURATION):
        return cls(site, configuration['www_directory_path'], configuration['https'])

    async def post_generate(self) -> None:
        await self._generate_config()

    @property
    def assets_directory_path(self) -> Optional[str]:
        return '%s/assets' % os.path.dirname(__file__)

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

    async def _generate_config(self) -> None:
        output_directory_path = os.path.join(self._site.configuration.output_directory_path, 'nginx')
        makedirs(output_directory_path)

        # Render the ngnix configuration.
        file_name = 'nginx.conf.j2'
        destination_file_path = os.path.join(output_directory_path, file_name)
        await self._site.assets.copy_file(file_name, destination_file_path)
        await self._site.renderer.render_directory(output_directory_path)

        # Render the Dockerfile.
        copyfile(os.path.join(DOCKER_PATH, 'Dockerfile'), os.path.join(output_directory_path, 'Dockerfile'))
