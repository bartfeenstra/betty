from contextlib import suppress

import docker
from docker.errors import NotFound
from docker.models.containers import Container as DockerContainer

from betty.os import PathLike


class Container:
    def __init__(self, www_directory_path: PathLike, docker_directory_path: PathLike, nginx_configuration_file_path: PathLike, name: str):
        self._name = name
        self._docker_directory_path = docker_directory_path
        self._nginx_configuration_file_path = nginx_configuration_file_path
        self._www_directory_path = www_directory_path
        self._client = docker.from_env()

    def __enter__(self) -> None:
        self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def start(self) -> None:
        # Stop any containers that may have been left over.
        self.stop()

        self._client.images.build(path=str(self._docker_directory_path), tag=self._name)
        self._client.containers.run(self._name, name=self._name, auto_remove=True, detach=True, volumes={
            self._nginx_configuration_file_path: {
                'bind': '/etc/nginx/conf.d/betty.conf',
                'mode': 'ro',
            },
            self._www_directory_path: {
                'bind': '/var/www/betty',
                'mode': 'ro',
            },
        })
        self._container.exec_run(['nginx', '-s', 'reload'])

    def stop(self) -> None:
        with suppress(NotFound):
            self._container.stop()

    @property
    def _container(self) -> DockerContainer:
        return self._client.containers.get(self._name)

    @property
    def ip(self) -> DockerContainer:
        return self._client.api.inspect_container(self._name)['NetworkSettings']['Networks']['bridge']['IPAddress']
