from pytest_mock import MockerFixture

from betty.app import App
from betty.test_utils.cli import run


class TestDevNewTranslation:
    async def test_click_command(
        self, mocker: MockerFixture, new_temporary_app: App
    ) -> None:
        locale = "nl-NL"
        m_new_translation = mocker.patch("betty.locale.translation.new_dev_translation")
        await run(new_temporary_app, "dev-new-translation", locale)
        m_new_translation.assert_awaited_once_with(locale)

    async def test_click_command_with_invalid_locale(
        self, new_temporary_app: App
    ) -> None:
        await run(
            new_temporary_app,
            "dev-new-translation",
            "",
            expected_exit_code=2,
        )
