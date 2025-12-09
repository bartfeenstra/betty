import pytest
from pytest_mock import MockerFixture
from typing_extensions import override

from betty.app import App
from betty.console import SystemExitCode
from betty.console.command import Command
from betty.console.command.commands.docs import Docs
from betty.plugin import PluginDefinition
from betty.test_utils.console import run
from betty.test_utils.console.command import CommandDefinitionTestBase, CommandTestBase
from betty.test_utils.serve import NoOpServer


class TestDocsDefinition(CommandDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Docs.plugin()


class TestDocs(CommandTestBase):
    @override
    @pytest.fixture
    def sut(self, isolated_app: App) -> Command:
        return Docs(isolated_app)

    async def test_configure(self, mocker: MockerFixture, isolated_app: App) -> None:
        mocker.patch("asyncio.sleep", side_effect=KeyboardInterrupt)
        mocker.patch("betty.documentation.DocumentationServer", new=NoOpServer)

        await run(isolated_app, "docs", expected_exit_code=SystemExitCode.USER_QUIT)
