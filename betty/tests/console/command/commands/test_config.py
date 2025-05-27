from pathlib import Path

from pytest_mock import MockerFixture
from typing_extensions import override

from betty.app import App
from betty.app.config import AppConfiguration
from betty.config.file import assert_configuration_file
from betty.console.command import Command
from betty.console.command.commands.config import Config
from betty.test_utils.console import run
from betty.test_utils.plugin import PluginTestBase


class TestConfig(PluginTestBase[Command]):
    @override
    def get_sut_class(self) -> type[Command]:
        return Config

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
