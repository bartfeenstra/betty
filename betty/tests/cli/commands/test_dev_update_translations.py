from betty.app import App
from betty.test_utils.cli import run
from pytest_mock import MockerFixture


class TestDevUpdateTranslations:
    async def test(self, mocker: MockerFixture, new_temporary_app: App) -> None:
        m_update_translations = mocker.patch(
            "betty.locale.translation.update_dev_translations"
        )
        await run(new_temporary_app, "dev-update-translations")
        m_update_translations.assert_awaited_once()
