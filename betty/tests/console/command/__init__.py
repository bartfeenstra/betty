from collections.abc import AsyncIterator
from pathlib import Path

import pytest

from betty.app import App
from betty.plugin.discovery.static import StaticDiscovery
from betty.project.extension import Extension, ExtensionDefinition


class ExtensionTranslationTestBase:
    @pytest.fixture
    async def isolated_app_with_extensions(
        self, tmp_path: Path, isolated_app: App
    ) -> AsyncIterator[App]:
        @ExtensionDefinition("dummy-without-assets", label="Dummy without assets")
        class _DummyWithoutAssetsDirectoryExtension(Extension):
            pass

        @ExtensionDefinition(
            "dummy-with-assets",
            label="Dummy with assets",
            assets_directory_path=tmp_path / "assets",
        )
        class _DummyWithAssetsDirectoryExtension(Extension):
            pass

        with ExtensionDefinition.type().override_discovery(
            StaticDiscovery(
                _DummyWithoutAssetsDirectoryExtension.plugin(),
                _DummyWithAssetsDirectoryExtension.plugin(),
            )
        ):
            yield isolated_app
