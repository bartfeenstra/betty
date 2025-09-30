from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from betty.locale.localizable import Plain
from betty.plugin.static import StaticPluginRepository
from betty.project.extension import Extension, ExtensionDefinition


class ExtensionTranslationTestBase:
    @pytest.fixture(autouse=True)
    def _extensions(self, mocker: MockerFixture, tmp_path: Path) -> None:
        @ExtensionDefinition(
            id="dummy-without-assets",
            label=Plain("Dummy without assets"),
        )
        class _DummyWithoutAssetsDirectoryExtension(Extension):
            pass

        @ExtensionDefinition(
            id="dummy-with-assets",
            label=Plain("Dummy with assets"),
            assets_directory_path=tmp_path / "assets",
        )
        class _DummyWithAssetsDirectoryExtension(Extension):
            pass

        mocker.patch(
            "betty.project.extension.EXTENSION_REPOSITORY",
            new=StaticPluginRepository(
                ExtensionDefinition,
                _DummyWithoutAssetsDirectoryExtension.plugin,
                _DummyWithAssetsDirectoryExtension.plugin,
            ),
        )
