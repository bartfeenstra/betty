from os import path
from typing import Optional, Any, Iterable
from urllib.parse import urlparse

from voluptuous import Schema, Required, Maybe

from betty.generate import Generator
from betty.extension import Extension, NO_CONFIGURATION
from betty.extension.nginx.artifact import generate_configuration_file, generate_dockerfile_file
from betty.serve import ServerProvider, Server
from betty.app import App


class Nginx(Extension, Generator, ServerProvider):
    configuration_schema: Schema = Schema({
        Required('www_directory_path', default=None): Maybe(str),
        Required('https', default=None): Maybe(bool),
    })

    def __init__(self, app: App, www_directory_path: Optional[str] = None, https: Optional[bool] = None):
        self._https = https
        self._www_directory_path = www_directory_path
        self._app = app

    @classmethod
    def new_for_app(cls, app: App, configuration: Any = NO_CONFIGURATION):
        return cls(app, configuration['www_directory_path'], configuration['https'])

    @property
    def servers(self) -> Iterable[Server]:
        from betty.extension.nginx.serve import DockerizedNginxServer

        if DockerizedNginxServer.is_available():
            return [DockerizedNginxServer(self._app)]
        return []

    async def generate(self) -> None:
        await self.generate_configuration_file()
        await self._generate_dockerfile_file()

    @property
    def assets_directory_path(self) -> Optional[str]:
        return '%s/assets' % path.dirname(__file__)

    @property
    def https(self) -> bool:
        if self._https is None:
            return self._app.configuration.base_url.startswith('https')
        return self._https

    @property
    def www_directory_path(self) -> str:
        if self._www_directory_path is None:
            return self._app.configuration.www_directory_path
        return self._www_directory_path

    async def generate_configuration_file(self, destination_file_path: Optional[str] = None, **kwargs) -> None:
        kwargs = dict({
            'content_negotiation': self._app.configuration.content_negotiation,
            'https': self.https,
            'locale': self._app.locale,
            'locales': self._app.configuration.locales,
            'multilingual': self._app.configuration.multilingual,
            'server_name': urlparse(self._app.configuration.base_url).netloc,
            'www_directory_path': self.www_directory_path,
        }, **kwargs)
        if destination_file_path is None:
            destination_file_path = path.join(self._app.configuration.output_directory_path, 'nginx', 'nginx.conf')
        await generate_configuration_file(destination_file_path, self._app.jinja2_environment, **kwargs)

    async def _generate_dockerfile_file(self) -> None:
        await generate_dockerfile_file(path.join(self._app.configuration.output_directory_path, 'nginx', 'docker', 'Dockerfile'))
