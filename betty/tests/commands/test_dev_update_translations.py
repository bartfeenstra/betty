from pytest_mock import MockerFixture

from betty.app import App
from betty.test_utils.console import run


class TestDevUpdateTranslations:
    async def test_configure(self, mocker: MockerFixture, isolated_app: App) -> None:
        m_update_builtin_translations = mocker.patch(
            "betty.gettext.update_builtin_translations"
        )
        await run(isolated_app, "dev-update-translations")
        m_update_builtin_translations.assert_awaited_once()
