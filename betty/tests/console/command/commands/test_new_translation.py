from unittest.mock import ANY

import pytest
from pytest_mock import MockerFixture
from typing_extensions import override

from betty.app import App
from betty.config.file import write_configuration_file
from betty.console import SystemExitCode
from betty.console.command.commands.new_translation import NewTranslation
from betty.plugin import PluginDefinition
from betty.project import Project
from betty.test_utils.console import run
from betty.test_utils.console.command import CommandDefinitionTestBase


class TestNewTranslationsDefinition(CommandDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return NewTranslation.plugin


class TestNewTranslation:
    async def test_configure__minimal(
        self, mocker: MockerFixture, temporary_app: App
    ) -> None:
        async with Project.new_temporary(temporary_app) as project, project:
            await write_configuration_file(
                project.configuration, project.configuration.configuration_file_path
            )
            locale = "nl-NL"
            m_new_translation = mocker.patch(
                "betty.locale.translation.project.new_project_translation"
            )
            await run(
                temporary_app,
                "new-translation",
                "--project",
                str(project.configuration.configuration_file_path),
                locale,
            )
            m_new_translation.assert_awaited_once_with(locale, ANY, user=ANY)

    async def test_configure__with_invalid_locale(self, temporary_app: App) -> None:
        await run(
            temporary_app,
            "new-translation",
            "",
            expected_exit_code=SystemExitCode.ERROR_CONSOLE_USAGE,
        )
