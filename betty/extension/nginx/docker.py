import asyncio
from pathlib import Path
from types import TracebackType

import docker
from docker.models.containers import Container as DockerContainer


class Container:
    _IMAGE_TAG = 'betty-serve'

    def __init__(self, www_directory_path: Path, docker_directory_path: Path, nginx_configuration_file_path: Path):
        self._docker_directory_path = docker_directory_path
        self._nginx_configuration_file_path = nginx_configuration_file_path
        self._www_directory_path = www_directory_path
        self._client = docker.from_env()
        self.__container: DockerContainer | None = None

    async def __aenter__(self) -> None:
        await self.start()

    async def __aexit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None) -> None:
        await self.stop()

    async def start(self) -> None:
        await asyncio.to_thread(self._start)

    def _start(self) -> None:
        self._client.images.build(path=str(self._docker_directory_path), tag=self._IMAGE_TAG)
        self._container.start()
        self._container.exec_run(['nginx', '-s', 'reload'])

    async def stop(self) -> None:
        await asyncio.to_thread(self._stop)

    def _stop(self) -> None:
        if self._container is not None:
            self._container.stop()

    @property
    def _container(self) -> DockerContainer:
        if self.__container is None:
            self.__container = self._client.containers.create(
                self._IMAGE_TAG,
                auto_remove=True,
                detach=True,
                volumes={
                    self._nginx_configuration_file_path: {
                        'bind': '/etc/nginx/conf.d/betty.conf',
                        'mode': 'ro',
                    },
                    self._www_directory_path: {
                        'bind': '/var/www/betty',
                        'mode': 'ro',
                    },
                },
            )
        return self.__container

    @property
    def ip(self) -> DockerContainer:
        return self._client.api.inspect_container(self._container.id)['NetworkSettings']['Networks']['bridge']['IPAddress']
