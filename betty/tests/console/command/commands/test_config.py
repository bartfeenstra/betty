from pathlib import Path

import pytest
from babel import Locale
from pytest_mock import MockerFixture
from typing_extensions import override

from betty.app import App
from betty.app.config import AppConfiguration
from betty.console.command.commands.config import Config
from betty.plugin import PluginDefinition
from betty.serde.file import assert_load_file
from betty.test_utils.console import run
from betty.test_utils.console.command import CommandPluginTestBase


class TestConfigDefinition(CommandPluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Config.plugin


class TestConfig:
    async def test_configure__with_locale(
        self, mocker: MockerFixture, isolated_app: App, tmp_path: Path
    ) -> None:
        configuration_file_path = tmp_path / "app.json"
        mocker.patch(
            "betty.app.config.CONFIGURATION_FILE_PATH",
            new=configuration_file_path,
        )

        locale = "nl"
        await run(
            isolated_app,
            "config",
            "--locale",
            locale,
        )
        configuration = AppConfiguration.load(
            (await assert_load_file())(configuration_file_path)
        )
        assert configuration.locale == Locale(locale)
