import pytest
from pytest_mock import MockerFixture
from typing_extensions import override

from betty.app import App
from betty.console.command.commands.dev_update_translations import DevUpdateTranslations
from betty.plugin import PluginDefinition
from betty.test_utils.console import run
from betty.test_utils.console.command import CommandDefinitionTestBase


class TestDevUpdateTranslationsDefinition(CommandDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return DevUpdateTranslations.plugin


class TestDevUpdateTranslations:
    async def test_configure(self, mocker: MockerFixture, temporary_app: App) -> None:
        m_update_translations = mocker.patch(
            "betty.locale.translation.update_dev_translations"
        )
        await run(temporary_app, "dev-update-translations")
        m_update_translations.assert_awaited_once()
