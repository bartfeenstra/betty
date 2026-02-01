from pathlib import Path

import pytest
from typing_extensions import override

from betty.extension import ExtensionDefinition
from betty.plugin import PluginDefinition
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE
from betty.test_utils.plugin import PluginDefinitionClassTestBase


class TestExtensionDefinition(PluginDefinitionClassTestBase):
    @override
    @pytest.fixture
    def sut(self) -> type[PluginDefinition]:
        return ExtensionDefinition

    def test_assets_directory_path(self) -> None:
        assets_directory_path = Path(__file__)
        sut = ExtensionDefinition(
            "-", assets_directory_path=assets_directory_path, label=DUMMY_LOCALIZABLE
        )
        assert sut.assets_directory_path == assets_directory_path

    def test_theme(self) -> None:
        sut = ExtensionDefinition("-", theme=True, label=DUMMY_LOCALIZABLE)
        assert sut.theme
