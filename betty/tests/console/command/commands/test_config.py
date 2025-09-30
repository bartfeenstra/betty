from pathlib import Path

import pytest
from pytest_mock import MockerFixture
from typing_extensions import override

from betty.app import App
from betty.app.config import AppConfiguration
from betty.config.file import assert_configuration_file
from betty.console.command.commands.config import Config
from betty.plugin import PluginDefinition
from betty.test_utils.console import run
from betty.test_utils.console.command import CommandDefinitionTestBase


class TestConfigDefinition(CommandDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Config.plugin


class TestConfig:
    async def test_configure__with_locale(
        self, mocker: MockerFixture, new_temporary_app: App, tmp_path: Path
    ) -> None:
        configuration_file_path = tmp_path / "app.json"
        mocker.patch(
            "betty.app.config.CONFIGURATION_FILE_PATH",
            new=configuration_file_path,
        )

        locale = "nl-NL"
        await run(
            new_temporary_app,
            "config",
            "--locale",
            locale,
        )
        configuration = AppConfiguration()
        (await assert_configuration_file(configuration))(configuration_file_path)
        assert configuration.locale == locale
