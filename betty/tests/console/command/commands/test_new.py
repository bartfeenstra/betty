from unittest.mock import ANY

from pytest_mock import MockerFixture
from typing_extensions import override

from betty.app import App
from betty.console.command import Command
from betty.console.command.commands.new import New
from betty.test_utils.console import run
from betty.test_utils.console.command import CommandTestBase


class TestNew(CommandTestBase):
    @override
    def get_sut_class(self) -> type[Command]:
        return New

    async def test_configure(
        self, new_temporary_app: App, mocker: MockerFixture
    ) -> None:
        m_new = mocker.patch("betty.project.new.new")
        await run(new_temporary_app, "new")
        m_new.assert_awaited_once_with(ANY)
