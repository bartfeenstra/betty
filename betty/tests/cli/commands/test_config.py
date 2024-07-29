from pathlib import Path

from betty.app import App
from betty.app.config import AppConfiguration
from betty.config import assert_configuration_file
from betty.test_utils.cli import run
from pytest_mock import MockerFixture


class TestConfig:
    async def test(
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
        assert_configuration_file(configuration)(configuration_file_path)
        assert configuration.locale == locale
