from __future__ import annotations

from pathlib import Path

import pytest

from betty.exception import HumanFacingException
from betty.locale.translation.project.extension import (
    assert_extension_assets_directory_path,
    assert_extension_has_assets_directory_path,
)
from betty.project.extension import Extension, ExtensionDefinition
from betty.test_utils.project.extension import DummyExtensionOne


@ExtensionDefinition(
    id="dummy-with-assets-directory",
    label="",
    assets_directory_path=Path(__file__),
)
class _DummyExtensionWithAssetsDirectory(Extension):
    pass


def test_assert_extension_assets_directory_path__without_assets_directory() -> None:
    with pytest.raises(HumanFacingException):
        assert_extension_assets_directory_path(DummyExtensionOne.plugin)


def test_assert_extension_assets_directory_path__with_assets_directory() -> None:
    assert (
        assert_extension_assets_directory_path(
            _DummyExtensionWithAssetsDirectory.plugin
        )
        == _DummyExtensionWithAssetsDirectory.plugin.assets_directory_path
    )


def test_assert_extension_has_assets_directory_path__without_assets_directory() -> None:
    with pytest.raises(HumanFacingException):
        assert_extension_has_assets_directory_path(DummyExtensionOne.plugin)


def test_assert_extension_has_assets_directory_path__with_assets_directory() -> None:
    assert (
        assert_extension_has_assets_directory_path(
            _DummyExtensionWithAssetsDirectory.plugin
        )
        == _DummyExtensionWithAssetsDirectory.plugin
    )
