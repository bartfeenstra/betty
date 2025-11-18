from collections.abc import AsyncIterator
from pathlib import Path

import pytest

from betty.app import App
from betty.locale.localizable import Plain
from betty.project.extension import Extension, ExtensionDefinition


class ExtensionTranslationTestBase:
    @pytest.fixture
    async def temporary_app_with_extensions(
        self, tmp_path: Path, temporary_app: App
    ) -> AsyncIterator[App]:
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

        with ExtensionDefinition.type.override_discoveries(
            _DummyWithoutAssetsDirectoryExtension.plugin,
            _DummyWithAssetsDirectoryExtension.plugin,
        ):
            yield temporary_app
