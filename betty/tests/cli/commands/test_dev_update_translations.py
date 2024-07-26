from asyncio import to_thread

from pytest_mock import MockerFixture

from betty.tests.cli.test___init__ import run


class TestDevUpdateTranslations:
    async def test(self, mocker: MockerFixture) -> None:
        m_update_translations = mocker.patch(
            "betty.locale.translation.update_dev_translations"
        )
        await to_thread(run, "dev-update-translations")
        m_update_translations.assert_awaited_once()
