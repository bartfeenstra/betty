"""
Integrate the nginx extension with Betty's Serve API.
"""
import logging
from pathlib import Path
from typing import Any

import docker
from aiofiles.tempfile import TemporaryDirectory, AiofilesContextManagerTempDir
from docker.errors import DockerException

from betty.app import App
from betty.extension.nginx.artifact import generate_dockerfile_file, generate_configuration_file
from betty.extension.nginx.docker import Container
from betty.project import Project
from betty.serve import NoPublicUrlBecauseServerNotStartedError, AppServer


class DockerizedNginxServer(AppServer):
    def __init__(self, app: App) -> None:
        from betty.extension import Nginx

        project = Project(ancestry=app.project.ancestry)
        project.configuration.autowrite = False
        project.configuration.configuration_file_path = app.project.configuration.configuration_file_path
        project.configuration.update(app.project.configuration)
        project.configuration.debug = True
        app = App(app.configuration, project)
        # Work around https://github.com/bartfeenstra/betty/issues/1056.
        app.extensions[Nginx].configuration.https = False
        super().__init__(app)
        self._container: Container | None = None
        self._output_directory: AiofilesContextManagerTempDir[None, Any, Any] | None = None

    async def start(self) -> None:
        await super().start()
        logging.getLogger(__name__).info('Starting a Dockerized nginx web server...')
        self._output_directory = TemporaryDirectory()
        output_directory_path_str = await self._output_directory.__aenter__()
        nginx_configuration_file_path = Path(output_directory_path_str) / 'nginx.conf'
        docker_directory_path = Path(output_directory_path_str)
        dockerfile_file_path = docker_directory_path / 'Dockerfile'

        await generate_configuration_file(
            self._app,
            destination_file_path=nginx_configuration_file_path,
            https=False,
            www_directory_path='/var/www/betty',
        )
        await generate_dockerfile_file(
            self._app,
            destination_file_path=dockerfile_file_path,
        )
        self._container = Container(
            self._app.project.configuration.www_directory_path,
            docker_directory_path,
            nginx_configuration_file_path,
        )
        await self._container.start()
        await self.assert_available()

    async def stop(self) -> None:
        if self._container is not None:
            await self._container.stop()
        if self._output_directory is not None:
            await self._output_directory.__aexit__(None, None, None)

    @property
    def public_url(self) -> str:
        if self._container is not None:
            return 'http://%s' % self._container.ip
        raise NoPublicUrlBecauseServerNotStartedError()

    @classmethod
    def is_available(cls) -> bool:
        try:
            docker.from_env().info()
            return True
        except DockerException as e:
            logging.getLogger(__name__).warning(e)
            return False
