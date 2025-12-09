from unittest.mock import ANY

import pytest
from babel import Locale
from pytest_mock import MockerFixture
from typing_extensions import override

from betty.app import App
from betty.console import SystemExitCode
from betty.console.command import Command
from betty.console.command.commands.extension_new_translation import (
    ExtensionNewTranslation,
)
from betty.plugin import PluginDefinition
from betty.test_utils.console import run
from betty.test_utils.console.command import CommandDefinitionTestBase, CommandTestBase
from betty.tests.console.command import ExtensionTranslationTestBase


class TestExtensionNewTranslationsDefinition(CommandDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return ExtensionNewTranslation.plugin()


class TestExtensionNewTranslation(ExtensionTranslationTestBase, CommandTestBase):
    @override
    @pytest.fixture
    def sut(self, isolated_app: App) -> Command:
        return ExtensionNewTranslation(isolated_app)

    async def test_configure__minimal(
        self,
        mocker: MockerFixture,
        isolated_app_with_extensions: App,
    ) -> None:
        locale = "nl"
        m_new_extension_translation = mocker.patch(
            "betty.locale.translation.project.extension.new_extension_translation"
        )
        await run(
            isolated_app_with_extensions,
            "extension-new-translation",
            "dummy-with-assets",
            locale,
        )
        m_new_extension_translation.assert_awaited_once_with(
            Locale(locale), ANY, user=ANY
        )

    async def test_configure__with_unknown_extension(
        self, isolated_app_with_extensions: App
    ) -> None:
        await run(
            isolated_app_with_extensions,
            "extension-new-translation",
            "unknown-extension-id",
            "nl-NL",
            expected_exit_code=SystemExitCode.ERROR_CONSOLE_USAGE,
        )

    async def test_configure__with_extension_without_assets_directory(
        self, isolated_app_with_extensions: App
    ) -> None:
        await run(
            isolated_app_with_extensions,
            "extension-new-translation",
            "dummy-without-assets",
            "nl-NL",
            expected_exit_code=SystemExitCode.ERROR_CONSOLE_USAGE,
        )

    async def test_configure__with_invalid_locale(
        self, isolated_app_with_extensions: App
    ) -> None:
        await run(
            isolated_app_with_extensions,
            "extension-new-translation",
            "dummy-with-assets",
            "",
            expected_exit_code=SystemExitCode.ERROR_CONSOLE_USAGE,
        )
