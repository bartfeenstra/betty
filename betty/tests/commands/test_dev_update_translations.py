from pytest_mock import MockerFixture

from betty.app import App
from betty.commands._dev_update_translations import DevUpdateTranslations
from betty.test_utils.console import run


class TestDevUpdateTranslations:
    async def test_configure(self, isolated_app: App, mocker: MockerFixture) -> None:
        m_update_builtin_translations = mocker.patch(
            "betty.gettext.update_builtin_translations"
        )
        await run(DevUpdateTranslations(isolated_app), "dev-update-translations")
        m_update_builtin_translations.assert_awaited_once()
