from unittest.mock import ANY

from pytest_mock import MockerFixture

from betty.app import App
from betty.test_utils.cli import run
from betty.tests.cli.commands import ExtensionTranslationTestBase


class TestExtensionNewTranslation(ExtensionTranslationTestBase):
    async def test_click_command(
        self, mocker: MockerFixture, new_temporary_app: App
    ) -> None:
        locale = "nl-NL"
        m_new_extension_translation = mocker.patch(
            "betty.locale.translation.new_extension_translation"
        )
        await run(new_temporary_app, "extension-new-translation", "with-assets", locale)
        m_new_extension_translation.assert_awaited_once_with(locale, ANY)

    async def test_click_command_with_unknown_extension(
        self, new_temporary_app: App
    ) -> None:
        await run(
            new_temporary_app,
            "extension-new-translation",
            "unknown-extension-id",
            "nl-NL",
            expected_exit_code=2,
        )

    async def test_click_command_with_extension_without_assets_directory(
        self, new_temporary_app: App
    ) -> None:
        await run(
            new_temporary_app,
            "extension-new-translation",
            "without-assets",
            "nl-NL",
            expected_exit_code=2,
        )

    async def test_click_command_with_invalid_locale(
        self, new_temporary_app: App
    ) -> None:
        await run(
            new_temporary_app,
            "extension-new-translation",
            "with-assets",
            "",
            expected_exit_code=2,
        )
