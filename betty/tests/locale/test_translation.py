from __future__ import annotations

from pathlib import Path

import pytest
from typing_extensions import override

from betty.error import UserFacingError
from betty.fs import ASSETS_DIRECTORY_PATH
from betty.locale.translation import (
    update_dev_translations,
    assert_extension_assets_directory_path,
)
from betty.test_utils.locale import PotFileTestBase
from betty.test_utils.project.extension import DummyExtension


class TestAssertExtensionAssetsDirectoryPath:
    class _DummyExtensionWithAssetsDirectory(DummyExtension):
        @override
        @classmethod
        def assets_directory_path(cls) -> Path | None:
            return Path(__file__)

    def test_without_assets_directory(self) -> None:
        with pytest.raises(UserFacingError):
            assert_extension_assets_directory_path(DummyExtension)

    def test_with_assets_directory(self) -> None:
        assert (
            assert_extension_assets_directory_path(
                self._DummyExtensionWithAssetsDirectory
            )
            == self._DummyExtensionWithAssetsDirectory.assets_directory_path()
        )


class TestPotFile(PotFileTestBase):
    @override
    def assets_directory_path(self) -> Path:
        return ASSETS_DIRECTORY_PATH

    @override
    def command(self) -> str:
        return "betty dev-update-translations"  # pragma: no cover

    @override
    async def update_translations(
        self, output_assets_directory_path_override: Path
    ) -> None:
        await update_dev_translations(
            _output_assets_directory_path_override=output_assets_directory_path_override
        )
