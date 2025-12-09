from unittest.mock import ANY

import pytest
from pytest_mock import MockerFixture
from typing_extensions import override

from betty.app import App
from betty.console.command import Command
from betty.console.command.commands.new import New
from betty.plugin import PluginDefinition
from betty.test_utils.console import run
from betty.test_utils.console.command import CommandDefinitionTestBase, CommandTestBase


class TestNewDefinition(CommandDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return New.plugin()


class TestNew(CommandTestBase):
    @override
    @pytest.fixture
    def sut(self, isolated_app: App) -> Command:
        return New(isolated_app)

    async def test_configure(self, isolated_app: App, mocker: MockerFixture) -> None:
        m_new = mocker.patch("betty.project.new.new")
        await run(isolated_app, "new")
        m_new.assert_awaited_once_with(ANY)
