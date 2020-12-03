import logging
from os import path
from tempfile import TemporaryDirectory

import docker
from docker.errors import DockerException

from betty.plugin.nginx import Nginx, generate_dockerfile_file
from betty.plugin.nginx.docker import Container
from betty.serve import Server, ServerNotStartedError
from betty.site import Site


class DockerizedNginxServer(Server):
    def __init__(self, site: Site):
        self._site = site
        self._container = None
        self._output_directory = None

    async def start(self) -> None:
        logging.getLogger().info('Starting a Dockerized nginx web server...')
        self._output_directory = TemporaryDirectory()
        nginx_configuration_file_path = path.join(self._output_directory.name, 'nginx.conf')
        docker_directory_path = path.join(self._output_directory.name, 'docker')
        dockerfile_file_path = path.join(docker_directory_path, 'Dockerfile')
        async with self._site:
            await self._site.plugins[Nginx].generate_configuration_file(destination_file_path=nginx_configuration_file_path, https=False, www_directory_path='/var/www/betty')
            await generate_dockerfile_file(destination_file_path=dockerfile_file_path)
        self._container = Container(self._site.configuration.www_directory_path, docker_directory_path, nginx_configuration_file_path, 'betty-serve')
        self._container.start()

    async def stop(self) -> None:
        self._container.stop()
        self._output_directory.cleanup()

    @property
    def public_url(self) -> str:
        if self._container is not None:
            return 'http://%s' % self._container.ip
        raise ServerNotStartedError('Cannot determine the public URL if the server has not started yet.')

    @classmethod
    def is_available(cls) -> bool:
        try:
            docker.from_env().info()
            return True
        except DockerException as e:
            logging.getLogger().warning(e)
            return False
