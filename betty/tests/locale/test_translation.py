from __future__ import annotations

from pathlib import Path

import pytest
from typing_extensions import override

from betty.exception import UserFacingException
from betty.fs import ASSETS_DIRECTORY_PATH
from betty.locale.translation import (
    assert_extension_assets_directory_path,
    assert_extension_has_assets_directory_path,
    update_dev_translations,
)
from betty.test_utils.locale import PotFileTestBase
from betty.test_utils.project.extension import DummyExtension


class _DummyExtensionWithAssetsDirectory(DummyExtension):
    @override
    @classmethod
    def assets_directory_path(cls) -> Path | None:
        return Path(__file__)


def test_assert_extension_assets_directory_path__without_assets_directory() -> None:
    with pytest.raises(UserFacingException):
        assert_extension_assets_directory_path(DummyExtension)


def test_assert_extension_assets_directory_path__with_assets_directory() -> None:
    assert (
        assert_extension_assets_directory_path(_DummyExtensionWithAssetsDirectory)
        == _DummyExtensionWithAssetsDirectory.assets_directory_path()
    )


def test_assert_extension_has_assets_directory_path__without_assets_directory() -> None:
    with pytest.raises(UserFacingException):
        assert_extension_has_assets_directory_path(DummyExtension)


def test_assert_extension_has_assets_directory_path__with_assets_directory() -> None:
    assert (
        assert_extension_has_assets_directory_path(_DummyExtensionWithAssetsDirectory)
        == _DummyExtensionWithAssetsDirectory
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
