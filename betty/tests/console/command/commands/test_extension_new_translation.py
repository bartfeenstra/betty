from unittest.mock import ANY

from pytest_mock import MockerFixture
from typing_extensions import override

from betty.app import App
from betty.console import SystemExitCode
from betty.console.command import Command
from betty.console.command.commands.extension_new_translation import (
    ExtensionNewTranslation,
)
from betty.test_utils.console import run
from betty.test_utils.console.command import CommandTestBase
from betty.tests.console.command import ExtensionTranslationTestBase


class TestExtensionNewTranslation(ExtensionTranslationTestBase, CommandTestBase):
    @override
    def get_sut_class(self) -> type[Command]:
        return ExtensionNewTranslation

    async def test_configure__minimal(
        self, mocker: MockerFixture, new_temporary_app: App
    ) -> None:
        locale = "nl-NL"
        m_new_extension_translation = mocker.patch(
            "betty.locale.translation.new_extension_translation"
        )
        await run(
            new_temporary_app,
            "extension-new-translation",
            "dummy-with-assets-directory-extension",
            locale,
        )
        m_new_extension_translation.assert_awaited_once_with(locale, ANY, user=ANY)

    async def test_configure__with_unknown_extension(
        self, new_temporary_app: App
    ) -> None:
        await run(
            new_temporary_app,
            "extension-new-translation",
            "unknown-extension-id",
            "nl-NL",
            expected_exit_code=SystemExitCode.ERROR_CONSOLE_USAGE,
        )

    async def test_configure__with_extension_without_assets_directory(
        self, new_temporary_app: App
    ) -> None:
        await run(
            new_temporary_app,
            "extension-new-translation",
            "dummy-without-assets-directory-extension",
            "nl-NL",
            expected_exit_code=SystemExitCode.ERROR_CONSOLE_USAGE,
        )

    async def test_configure__with_invalid_locale(self, new_temporary_app: App) -> None:
        await run(
            new_temporary_app,
            "extension-new-translation",
            "dummy-with-assets-directory-extension",
            "",
            expected_exit_code=SystemExitCode.ERROR_CONSOLE_USAGE,
        )
