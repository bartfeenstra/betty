from __future__ import annotations

from pathlib import Path

from betty.assertions.path import assert_path


def test_assert_path__with_valid_str_path() -> None:
    assert_path()("~/../foo/bar")


def test_assert_path__with_valid_path_path() -> None:
    assert_path()(Path("~/../foo/bar"))
