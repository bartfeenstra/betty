import pytest
from aiofiles.os import makedirs
from pytest_mock import MockerFixture
from typing_extensions import override

from betty.app import App
from betty.console import SystemExitCode
from betty.console.command import Command
from betty.console.command.commands.serve import Serve
from betty.plugin import PluginDefinition
from betty.portable.file import dump_file
from betty.project import Project
from betty.test_utils.console import run
from betty.test_utils.console.command import CommandDefinitionTestBase, CommandTestBase
from betty.test_utils.serve import NoOpProjectServer


class TestServeDefinition(CommandDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Serve.plugin()


class TestServe(CommandTestBase):
    @override
    @pytest.fixture
    def sut(self, isolated_app: App) -> Command:
        return Serve(isolated_app)

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
