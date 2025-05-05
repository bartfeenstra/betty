from pytest_mock import MockerFixture
from typing_extensions import override

from betty.app import App
from betty.console import SystemExitCode
from betty.console.command import Command
from betty.console.command.commands.docs import Docs
from betty.test_utils.console import run
from betty.test_utils.console.command import CommandTestBase
from betty.test_utils.serve import NoOpServer


class TestDocs(CommandTestBase):
    @override
    def get_sut_class(self) -> type[Command]:
        return Docs

    async def test_configure(
        self, mocker: MockerFixture, new_temporary_app: App
    ) -> None:
        mocker.patch("asyncio.sleep", side_effect=KeyboardInterrupt)
        mocker.patch("betty.documentation.DocumentationServer", new=NoOpServer)

        await run(
            new_temporary_app, "docs", expected_exit_code=SystemExitCode.USER_QUIT
        )
