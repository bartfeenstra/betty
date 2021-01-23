from os import path
from typing import Optional, Iterable, Dict
from urllib.parse import urlparse

from voluptuous import Schema

from betty.generate import PostGenerator
from betty.plugin import Plugin
from betty.plugin.nginx.artifact import generate_configuration_file, generate_dockerfile_file
from betty.serve import ServerProvider, Server
from betty.site import Site


class Nginx(Plugin, PostGenerator, ServerProvider):
    configuration_schema: Schema = Schema({
        'www_directory_path': str,
        'https': bool,
    })

    def __init__(self, site: Site, www_directory_path: Optional[str] = None, https: Optional[bool] = None):
        self._https = https
        self._www_directory_path = www_directory_path
        self._site = site

    @classmethod
    def for_site(cls, site: Site, configuration: Dict):
        configuration.setdefault('www_directory_path', site.configuration.www_directory_path)
        configuration.setdefault('https', None)
        return cls(site, configuration['www_directory_path'], configuration['https'])

    @property
    def servers(self) -> Iterable[Server]:
        from betty.plugin.nginx.serve import DockerizedNginxServer

        if DockerizedNginxServer.is_available():
            return [DockerizedNginxServer(self._site)]
        return []

    async def post_generate(self) -> None:
        await self.generate_configuration_file()
        await self._generate_dockerfile_file()

    @property
    def assets_directory_path(self) -> Optional[str]:
        return '%s/assets' % path.dirname(__file__)

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

    async def generate_configuration_file(self, destination_file_path: Optional[str] = None, **kwargs) -> None:
        kwargs = dict({
            'content_negotiation': self._site.configuration.content_negotiation,
            'https': self._site.plugins[Nginx].https,
            'locale': self._site.locale,
            'locales': self._site.configuration.locales,
            'multilingual': self._site.configuration.multilingual,
            'server_name': urlparse(self._site.configuration.base_url).netloc,
            'www_directory_path': self._site.plugins[Nginx].www_directory_path,
        }, **kwargs)
        if destination_file_path is None:
            destination_file_path = path.join(self._site.configuration.output_directory_path, 'nginx', 'nginx.conf')
        await generate_configuration_file(destination_file_path, self._site.jinja2_environment, **kwargs)

    async def _generate_dockerfile_file(self) -> None:
        await generate_dockerfile_file(path.join(self._site.configuration.output_directory_path, 'nginx', 'docker', 'Dockerfile'))
