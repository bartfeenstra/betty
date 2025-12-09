import pytest
from pytest_mock import MockerFixture
from typing_extensions import override

from betty.app import App
from betty.console.command import Command
from betty.console.command.commands.dev_update_translations import DevUpdateTranslations
from betty.plugin import PluginDefinition
from betty.test_utils.console import run
from betty.test_utils.console.command import CommandDefinitionTestBase, CommandTestBase


class TestDevUpdateTranslationsDefinition(CommandDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return DevUpdateTranslations.plugin()


class TestDevUpdateTranslations(CommandTestBase):
    @override
    @pytest.fixture
    def sut(self, isolated_app: App) -> Command:
        return DevUpdateTranslations(isolated_app)

    async def test_configure(self, mocker: MockerFixture, isolated_app: App) -> None:
        m_update_translations = mocker.patch(
            "betty.locale.translation.update_dev_translations"
        )
        await run(isolated_app, "dev-update-translations")
        m_update_translations.assert_awaited_once()
