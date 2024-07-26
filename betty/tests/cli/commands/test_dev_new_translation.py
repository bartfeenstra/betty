from asyncio import to_thread

from pytest_mock import MockerFixture

from betty.tests.cli.test___init__ import run


class TestDevNewTranslation:
    async def test(self, mocker: MockerFixture) -> None:
        locale = "nl-NL"
        m_new_translation = mocker.patch("betty.locale.translation.new_dev_translation")
        await to_thread(run, "dev-new-translation", locale)
        m_new_translation.assert_awaited_once_with(locale)

    async def test_without_locale_arg(self) -> None:
        await to_thread(run, "dev-new-translation", expected_exit_code=2)
