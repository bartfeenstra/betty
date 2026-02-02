from collections.abc import AsyncIterator
from pathlib import Path

import pytest

from betty.app import App
from betty.extension import Extension, ExtensionDefinition


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
            assets_directory=tmp_path / "assets",
        )
        class _DummyWithAssetsDirectoryExtension(Extension):
            pass

        with ExtensionDefinition.type().discoverer.override(
            _DummyWithoutAssetsDirectoryExtension,
            _DummyWithAssetsDirectoryExtension,
        ):
            yield isolated_app
