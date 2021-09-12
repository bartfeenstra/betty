import docker
from docker.models.containers import Container as DockerContainer

from betty.os import PathLike


class Container:
    _IMAGE_TAG = 'betty-serve'

    def __init__(self, www_directory_path: PathLike, docker_directory_path: PathLike, nginx_configuration_file_path: PathLike):
        self._docker_directory_path = docker_directory_path
        self._nginx_configuration_file_path = nginx_configuration_file_path
        self._www_directory_path = www_directory_path
        self._client = docker.from_env()
        self._container = None

    def __enter__(self) -> None:
        self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def start(self) -> None:
        self._client.images.build(path=str(self._docker_directory_path), tag=self._IMAGE_TAG)
        self._container = self._client.containers.create(self._IMAGE_TAG, auto_remove=True, detach=True, volumes={
            self._nginx_configuration_file_path: {
                'bind': '/etc/nginx/conf.d/betty.conf',
                'mode': 'ro',
            },
            self._www_directory_path: {
                'bind': '/var/www/betty',
                'mode': 'ro',
            },
        })
        self._container.start()
        self._container.exec_run(['nginx', '-s', 'reload'])

    def stop(self) -> None:
        self._container.stop()

    @property
    def ip(self) -> DockerContainer:
        return self._client.api.inspect_container(self._container.id)['NetworkSettings']['Networks']['bridge']['IPAddress']
