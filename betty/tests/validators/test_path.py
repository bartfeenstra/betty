from __future__ import annotations

from pathlib import Path

from betty.validators.path import is_path


def test_is_path__with_valid_str_path() -> None:
    is_path()("~/../foo/bar")


def test_is_path__with_valid_path_path() -> None:
    is_path()(Path("~/../foo/bar"))
