from asyncio import to_thread

from aiofiles.os import makedirs
from pytest_mock import MockerFixture

from betty.app import App
from betty.extension import Nginx
from betty.extension.nginx.serve import DockerizedNginxServer
from betty.tests.test_cli import run, NoOpServer


class KeyboardInterruptedDockerizedNginxServer(DockerizedNginxServer):
    async def start(self) -> None:
        raise KeyboardInterrupt()


class TestServe:
    async def test(self, mocker: MockerFixture, new_temporary_app: App) -> None:
        mocker.patch("asyncio.sleep", side_effect=KeyboardInterrupt)
        mocker.patch(
            "betty.extension.nginx.serve.DockerizedNginxServer", new=NoOpServer
        )
        new_temporary_app.project.configuration.extensions.enable(Nginx)
        await new_temporary_app.project.configuration.write()
        await makedirs(new_temporary_app.project.configuration.www_directory_path)

        await to_thread(
            run,
            "-c",
            str(new_temporary_app.project.configuration.configuration_file_path),
            "serve-nginx-docker",
        )
