from asyncio import to_thread

from pytest_mock import MockerFixture

from betty.tests.cli.test___init__ import run


class TestInitTranslation:
    async def test(self, mocker: MockerFixture) -> None:
        locale = "nl-NL"
        m_init_translation = mocker.patch("betty.locale.init_translation")
        await to_thread(run, "init-translation", locale)
        m_init_translation.assert_awaited_once_with(locale)

    async def test_without_locale_arg(self) -> None:
        await to_thread(run, "init-translation", expected_exit_code=2)
