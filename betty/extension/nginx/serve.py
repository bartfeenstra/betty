import logging
from pathlib import Path
from tempfile import TemporaryDirectory

import docker
from docker.errors import DockerException

from betty.extension.nginx import generate_dockerfile_file, generate_configuration_file
from betty.extension.nginx.docker import Container
from betty.serve import Server, NoPublicUrlBecauseServerNotStartedError
from betty.app import App


class DockerizedNginxServer(Server):
    def __init__(self, app: App):
        self._app = app.with_debug(True)
        self._container = None
        self._output_directory = None

    async def start(self) -> None:
        logging.getLogger().info('Starting a Dockerized nginx web server...')
        self._output_directory = TemporaryDirectory()
        nginx_configuration_file_path = Path(self._output_directory.name) / 'nginx.conf'
        docker_directory_path = Path(self._output_directory.name) / 'docker'
        dockerfile_file_path = docker_directory_path / 'Dockerfile'
        async with self._app:
            await generate_configuration_file(self._app, destination_file_path=nginx_configuration_file_path, https=False, www_directory_path='/var/www/betty')
            await generate_dockerfile_file(self._app, destination_file_path=dockerfile_file_path)
        self._container = Container(self._app.configuration.www_directory_path, docker_directory_path, nginx_configuration_file_path, 'betty-serve')
        self._container.start()

    async def stop(self) -> None:
        self._container.stop()
        self._output_directory.cleanup()

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
