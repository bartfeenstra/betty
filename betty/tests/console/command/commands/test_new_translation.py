from unittest.mock import ANY

import pytest
from babel import Locale
from pytest_mock import MockerFixture
from typing_extensions import override

from betty.app import App
from betty.console import SystemExitCode
from betty.console.command import Command
from betty.console.command.commands.new_translation import NewTranslation
from betty.plugin import PluginDefinition
from betty.portable.file import dump_file
from betty.project import Project
from betty.test_utils.console import run
from betty.test_utils.console.command import CommandDefinitionTestBase, CommandTestBase


class TestNewTranslationsDefinition(CommandDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return NewTranslation.plugin()


class TestNewTranslation(CommandTestBase):
    @override
    @pytest.fixture
    def sut(self, isolated_app: App) -> Command:
        return NewTranslation(isolated_app)

    async def test_configure__minimal(
        self, mocker: MockerFixture, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            await dump_file(
                project.configuration.data().dump(project.configuration),
                project.configuration_file_path,
            )
            locale = "nl"
            m_new_translation = mocker.patch(
                "betty.locale.translation.project.new_project_translation"
            )
            await run(
                isolated_app,
                "new-translation",
                "--project",
                str(project.configuration_file_path),
                locale,
            )
            m_new_translation.assert_awaited_once_with(Locale(locale), ANY, user=ANY)

    async def test_configure__with_invalid_locale(self, isolated_app: App) -> None:
        await run(
            isolated_app,
            "new-translation",
            "",
            expected_exit_code=SystemExitCode.ERROR_CONSOLE_USAGE,
        )
