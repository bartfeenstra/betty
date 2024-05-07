"""
Integrate the nginx extension with Betty's Serve API.
"""

import logging
from contextlib import AsyncExitStack
from pathlib import Path

import docker
from aiofiles.tempfile import TemporaryDirectory
from docker.errors import DockerException

from betty.app import App
from betty.extension.nginx.artifact import (
    generate_dockerfile_file,
    generate_configuration_file,
)
from betty.extension.nginx.docker import Container
from betty.project import Project
from betty.serve import NoPublicUrlBecauseServerNotStartedError, Server


class DockerizedNginxServer(Server):
    def __init__(self, app: App) -> None:
        super().__init__(app.localizer)
        self._app = app
        self._exit_stack = AsyncExitStack()
        self._container: Container | None = None

    async def start(self) -> None:
        from betty.extension import Nginx

        await super().start()
        logging.getLogger(__name__).info("Starting a Dockerized nginx web server...")

        output_directory_path_str = await self._exit_stack.enter_async_context(
            TemporaryDirectory()
        )

        isolated_project = Project(ancestry=self._app.project.ancestry)
        isolated_project.configuration.autowrite = False
        isolated_project.configuration.configuration_file_path = (
            self._app.project.configuration.configuration_file_path
        )
        isolated_project.configuration.update(self._app.project.configuration)
        isolated_project.configuration.debug = True

        isolated_app = await self._exit_stack.enter_async_context(
            App.new_from_app(self._app, project=isolated_project)
        )
        await self._exit_stack.enter_async_context(isolated_app)
        isolated_app.configuration.update(self._app.configuration)
        # Work around https://github.com/bartfeenstra/betty/issues/1056.
        isolated_app.extensions[Nginx].configuration.https = False

        nginx_configuration_file_path = Path(output_directory_path_str) / "nginx.conf"
        docker_directory_path = Path(output_directory_path_str)
        dockerfile_file_path = docker_directory_path / "Dockerfile"

        await generate_configuration_file(
            isolated_app,
            destination_file_path=nginx_configuration_file_path,
            https=False,
            www_directory_path="/var/www/betty",
        )
        await generate_dockerfile_file(
            isolated_app,
            destination_file_path=dockerfile_file_path,
        )
        self._container = Container(
            isolated_app.project.configuration.www_directory_path,
            docker_directory_path,
            nginx_configuration_file_path,
        )
        await self._exit_stack.enter_async_context(self._container)
        await self.assert_available()

    async def stop(self) -> None:
        await self._exit_stack.aclose()

    @property
    def public_url(self) -> str:
        if self._container is not None:
            return "http://%s" % self._container.ip
        raise NoPublicUrlBecauseServerNotStartedError()

    @classmethod
    def is_available(cls) -> bool:
        try:
            docker.from_env()
            return True
        except DockerException as e:
            logging.getLogger(__name__).warning(e)
            return False
