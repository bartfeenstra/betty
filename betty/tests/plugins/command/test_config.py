from pathlib import Path

from babel import Locale
from pytest_mock import MockerFixture

from betty.app import App
from betty.app.data import AppConfiguration
from betty.plugins.serializer.json import Json
from betty.portable.file import assert_load_file
from betty.test_utils.console import run


class TestConfig:
    async def test_configure__with_locale(
        self, mocker: MockerFixture, isolated_app: App, tmp_path: Path
    ) -> None:
        configuration_file = tmp_path / "app.json"
        mocker.patch("betty.app.data.AppConfiguration.FILE", new=configuration_file)

        locale = "nl"
        await run(
            isolated_app,
            "config",
            "--locale",
            locale,
        )
        configuration = AppConfiguration.data().porter.load(
            assert_load_file(serializers=[Json()])(configuration_file)
        )
        assert configuration.locale == Locale(locale)
