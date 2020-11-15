import logging
from contextlib import suppress
from os import path

import docker
from docker.errors import DockerException, NotFound
from docker.models.containers import Container

from betty.error import UserFacingError
from betty.serve import Server


class DockerError(UserFacingError, RuntimeError):
    pass


class DockerizedNginxServer(Server):
    _TAG = 'betty-serve'

    def __init__(self, www_directory_path: str, output_directory_path: str):
        self._www_directory_path = www_directory_path
        self._output_directory_path = output_directory_path
        self._client = docker.from_env()

    @property
    def public_url(self) -> str:
        if self._container is not None:
            return 'http://%s' % self._client.api.inspect_container(self._TAG)['NetworkSettings']['Networks']['bridge']['IPAddress']
        raise RuntimeError('Cannot determine the public URL until this server\'s context has been entered.')

    def __enter__(self) -> Server:
        # Stop any containers that may have been left over.
        self._stop()

        logging.getLogger().info('Starting a Dockerized nginx web server...')
        nginx_directory_path = path.join(self._output_directory_path, 'nginx')
        nginx_conf_file_path = path.join(nginx_directory_path, 'nginx.conf')
        self._client.images.build(path=nginx_directory_path, tag=self._TAG)
        self._client.containers.run(self._TAG, name=self._TAG, auto_remove=True, detach=True, volumes={
            nginx_conf_file_path: {
                'bind': '/etc/nginx/conf.d/betty.conf',
                'mode': 'ro',
            },
            self._www_directory_path: {
                'bind': '/var/www/betty',
                'mode': 'ro',
            },
        })
        self._container.exec_run(['nginx', '-s', 'reload'])
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._stop()

    def _stop(self) -> None:
        with suppress(NotFound):
            self._container.stop()

    @property
    def _container(self) -> Container:
        return self._client.containers.get(self._TAG)

    @classmethod
    def is_available(cls) -> bool:
        try:
            docker.from_env().info()
            return True
        except DockerException as e:
            logging.getLogger().warning(e)
            return False
