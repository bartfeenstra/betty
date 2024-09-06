from pathlib import Path

import pytest
from typing_extensions import override
from pytest_mock import MockerFixture

from betty.machine_name import MachineName
from betty.plugin.static import StaticPluginRepository
from betty.test_utils.project.extension import DummyExtension


class ExtensionTranslationTestBase:
    @pytest.fixture(autouse=True)
    def _extensions(self, mocker: MockerFixture, tmp_path: Path) -> None:
        class _DummyWithoutAssetsDirectoryExtension(DummyExtension):
            @override
            @classmethod
            def plugin_id(cls) -> MachineName:
                return "without-assets"

        class _DummyWithAssetsDirectoryExtension(DummyExtension):
            @override
            @classmethod
            def plugin_id(cls) -> MachineName:
                return "with-assets"

            @override
            @classmethod
            def assets_directory_path(cls) -> Path | None:
                return tmp_path / "assets"

        mocker.patch(
            "betty.project.extension.EXTENSION_REPOSITORY",
            new=StaticPluginRepository(
                _DummyWithoutAssetsDirectoryExtension,
                _DummyWithAssetsDirectoryExtension,
            ),
        )
