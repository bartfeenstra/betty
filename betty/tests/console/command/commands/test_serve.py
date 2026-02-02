from aiofiles.os import makedirs
from pytest_mock import MockerFixture

from betty.app import App
from betty.console import SystemExitCode
from betty.portable.file import dump_file
from betty.project import Project
from betty.test_utils.console import run
from betty.test_utils.serve import NoOpProjectServer


class TestServe:
    async def test_configure(self, mocker: MockerFixture, isolated_app: App) -> None:
        mocker.patch("asyncio.sleep", side_effect=KeyboardInterrupt)
        mocker.patch("betty.serve.BuiltinProjectServer", new=NoOpProjectServer)
        async with Project.new_isolated(isolated_app) as project:
            await dump_file(
                project.configuration.data().porter.dump(project.configuration),
                project.configuration_file,
            )
            await makedirs(project.www_directory)

            await run(
                isolated_app,
                "serve",
                "--project",
                str(project.configuration_file),
                expected_exit_code=SystemExitCode.USER_QUIT,
            )
