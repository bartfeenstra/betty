import pytest
from aiofiles.os import makedirs
from pytest_mock import MockerFixture
from typing_extensions import override

from betty.app import App
from betty.console import SystemExitCode
from betty.console.command.commands.serve import Serve
from betty.plugin import PluginDefinition
from betty.project import Project
from betty.serde.file import dump_file
from betty.test_utils.console import run
from betty.test_utils.console.command import CommandPluginTestBase
from betty.test_utils.serve import NoOpProjectServer


class TestServeDefinition(CommandPluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Serve.plugin


class TestServe:
    async def test_configure(self, mocker: MockerFixture, isolated_app: App) -> None:
        mocker.patch("asyncio.sleep", side_effect=KeyboardInterrupt)
        mocker.patch("betty.serve.BuiltinProjectServer", new=NoOpProjectServer)
        async with Project.new_isolated(isolated_app) as project:
            await dump_file(
                project.configuration.dump(), project.configuration_file_path
            )
            await makedirs(project.www_directory_path)

            await run(
                isolated_app,
                "serve",
                "--project",
                str(project.configuration_file_path),
                expected_exit_code=SystemExitCode.USER_QUIT,
            )
