from asyncio import to_thread

from aiofiles.os import makedirs
from pytest_mock import MockerFixture

from betty.app import App
from betty.config import write_configuration_file
from betty.project import Project
from betty.test_utils.cli import run
from betty.tests.cli.test___init__ import NoOpProjectServer


class TestServe:
    async def test(self, mocker: MockerFixture, new_temporary_app: App) -> None:
        mocker.patch("asyncio.sleep", side_effect=KeyboardInterrupt)
        mocker.patch("betty.serve.BuiltinProjectServer", new=NoOpProjectServer)
        async with Project.new_temporary(new_temporary_app) as project:
            await write_configuration_file(
                project.configuration, project.configuration.configuration_file_path
            )
            await makedirs(project.configuration.www_directory_path)

            await to_thread(
                run,
                "serve",
                "-c",
                str(project.configuration.configuration_file_path),
                expected_exit_code=1,
            )
