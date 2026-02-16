from pathlib import Path

from betty.extension import ExtensionDefinition
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE


class TestExtensionDefinition:
    def test_assets_directory(self) -> None:
        assets_directory_path = Path(__file__)
        sut = ExtensionDefinition(
            "-dummy", assets_directory=assets_directory_path, label=DUMMY_LOCALIZABLE
        )
        assert sut.assets_directory == assets_directory_path

    def test_theme(self) -> None:
        sut = ExtensionDefinition("-dummy", theme=True, label=DUMMY_LOCALIZABLE)
        assert sut.theme
