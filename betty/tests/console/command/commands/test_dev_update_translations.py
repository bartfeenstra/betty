from pytest_mock import MockerFixture
from typing_extensions import override

from betty.app import App
from betty.console.command import Command
from betty.console.command.commands.dev_update_translations import DevUpdateTranslations
from betty.test_utils.console import run
from betty.test_utils.console.command import CommandTestBase


class TestDevUpdateTranslations(CommandTestBase):
    @override
    def get_sut_class(self) -> type[Command]:
        return DevUpdateTranslations

    async def test_configure(
        self, mocker: MockerFixture, new_temporary_app: App
    ) -> None:
        m_update_translations = mocker.patch(
            "betty.locale.translation.update_dev_translations"
        )
        await run(new_temporary_app, "dev-update-translations")
        m_update_translations.assert_awaited_once()
