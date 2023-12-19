import logging
from pathlib import Path
from typing import Any

import dill
import docker
from aiofiles.tempfile import TemporaryDirectory, AiofilesContextManagerTempDir
from docker.errors import DockerException

from betty.app import App
from betty.extension.nginx.artifact import generate_dockerfile_file, generate_configuration_file
from betty.extension.nginx.docker import Container
from betty.serve import NoPublicUrlBecauseServerNotStartedError, AppServer


class DockerizedNginxServer(AppServer):
    def __init__(self, app: App) -> None:
        super().__init__(
            # Create a new app so we can modify it later.
            dill.loads(dill.dumps(app))
        )
        self._container: Container | None = None
        self._output_directory: AiofilesContextManagerTempDir[None, Any, Any] | None = None

    async def start(self) -> None:
        from betty.extension import Nginx

        await super().start()
        logging.getLogger().info('Starting a Dockerized nginx web server...')
        self._output_directory = TemporaryDirectory()
        output_directory_name = await self._output_directory.__aenter__()
        nginx_configuration_file_path = Path(output_directory_name) / 'nginx.conf'
        docker_directory_path = Path(output_directory_name) / 'docker'
        dockerfile_file_path = docker_directory_path / 'Dockerfile'

        self._app.project.configuration.debug = True
        # Work around https://github.com/bartfeenstra/betty/issues/1056.
        self._app.extensions[Nginx].configuration.https = False

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
            logging.getLogger().warning(e)
            return False
