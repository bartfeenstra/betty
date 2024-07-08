from asyncio import to_thread

from aiofiles.os import makedirs
from pytest_mock import MockerFixture

from betty.app import App
from betty.extension import Nginx
from betty.project import Project
from betty.tests.cli.test___init__ import run, NoOpServer


class TestServe:
    async def test(self, mocker: MockerFixture, new_temporary_app: App) -> None:
        mocker.patch("asyncio.sleep", side_effect=KeyboardInterrupt)
        mocker.patch(
            "betty.extension.nginx.serve.DockerizedNginxServer", new=NoOpServer
        )
        async with Project.new_temporary(new_temporary_app) as project:
            project.configuration.extensions.enable(Nginx)
            await project.configuration.write()
            await makedirs(project.configuration.www_directory_path)
            async with project:
                await to_thread(
                    run,
                    "serve-nginx-docker",
                    "-c",
                    str(project.configuration.configuration_file_path),
                )
