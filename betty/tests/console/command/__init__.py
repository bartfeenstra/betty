from collections.abc import AsyncIterator
from pathlib import Path

import pytest

from betty.app import App
from betty.locale.localizable import Plain
from betty.plugin.static import StaticPluginRepository
from betty.project.extension import Extension, ExtensionDefinition
from betty.test_utils.conftest import NewTemporaryAppFactory


class ExtensionTranslationTestBase:
    @pytest.fixture
    async def new_temporary_app_with_extensions(
        self, tmp_path: Path, new_temporary_app_factory: NewTemporaryAppFactory
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

        async with (
            new_temporary_app_factory(
                extension_repository=StaticPluginRepository(
                    ExtensionDefinition,
                    _DummyWithoutAssetsDirectoryExtension.plugin,
                    _DummyWithAssetsDirectoryExtension.plugin,
                )
            ) as app,
            app,
        ):
            yield app
