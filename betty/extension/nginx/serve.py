"""
Integrate the nginx extension with Betty's Serve API.
"""

import logging
from contextlib import AsyncExitStack
from pathlib import Path

import docker
from aiofiles.tempfile import TemporaryDirectory
from docker.errors import DockerException
from typing_extensions import override

from betty.extension.nginx.artifact import (
    generate_dockerfile_file,
    generate_configuration_file,
)
from betty.extension.nginx.docker import Container
from betty.project import Project
from betty.serve import NoPublicUrlBecauseServerNotStartedError, Server


class DockerizedNginxServer(Server):
    """
    An nginx server that runs within a Docker container.
    """

    def __init__(self, project: Project) -> None:
        super().__init__(project.app.localizer)
        self._project = project
        self._exit_stack = AsyncExitStack()
        self._container: Container | None = None

    @override
    async def start(self) -> None:
        from betty.extension import Nginx

        await super().start()
        logging.getLogger(__name__).info("Starting a Dockerized nginx web server...")

        output_directory_path_str: str = await self._exit_stack.enter_async_context(
            TemporaryDirectory()  # type: ignore[arg-type]
        )

        isolated_project = await self._exit_stack.enter_async_context(
            Project(self._project.app, ancestry=self._project.ancestry)
        )
        isolated_project.configuration.autowrite = False
        isolated_project.configuration.configuration_file_path = (
            self._project.configuration.configuration_file_path
        )
        isolated_project.configuration.update(self._project.configuration)
        isolated_project.configuration.debug = True

        # Work around https://github.com/bartfeenstra/betty/issues/1056.
        isolated_project.extensions[Nginx].configuration.https = False

        nginx_configuration_file_path = Path(output_directory_path_str) / "nginx.conf"
        docker_directory_path = Path(output_directory_path_str)
        dockerfile_file_path = docker_directory_path / "Dockerfile"

        await generate_configuration_file(
            isolated_project,
            destination_file_path=nginx_configuration_file_path,
            https=False,
            www_directory_path="/var/www/betty",
        )
        await generate_dockerfile_file(
            isolated_project,
            destination_file_path=dockerfile_file_path,
        )
        self._container = Container(
            isolated_project.configuration.www_directory_path,
            docker_directory_path,
            nginx_configuration_file_path,
        )
        await self._exit_stack.enter_async_context(self._container)
        await self.assert_available()

    @override
    async def stop(self) -> None:
        await self._exit_stack.aclose()

    @override
    @property
    def public_url(self) -> str:
        if self._container is not None:
            return "http://%s" % self._container.ip
        raise NoPublicUrlBecauseServerNotStartedError()

    @classmethod
    def is_available(cls) -> bool:
        """
        Check if Docker is available.
        """
        try:
            docker.from_env()
            return True
        except DockerException as e:
            logging.getLogger(__name__).warning(e)
            return False
