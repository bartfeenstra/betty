from collections.abc import AsyncIterator
from pathlib import Path

import pytest

from betty.app import App
from betty.project.extension import Extension, ExtensionPlugin


class ExtensionTranslationTestBase:
    @pytest.fixture
    async def temporary_app_with_extensions(
        self, tmp_path: Path, temporary_app: App
    ) -> AsyncIterator[App]:
        @ExtensionPlugin("dummy-without-assets", label="Dummy without assets")
        class _DummyWithoutAssetsDirectoryExtension(Extension):
            pass

        @ExtensionPlugin(
            "dummy-with-assets",
            label="Dummy with assets",
            assets_directory_path=tmp_path / "assets",
        )
        class _DummyWithAssetsDirectoryExtension(Extension):
            pass

        with ExtensionPlugin.type.override_discovery(
            _DummyWithoutAssetsDirectoryExtension.plugin,
            _DummyWithAssetsDirectoryExtension.plugin,
        ):
            yield temporary_app
