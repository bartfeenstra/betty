from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory

import pytest

from betty.validation import Invalid
from betty.validators.directory import is_directory


def test_is_directory__without_existing_path() -> None:
    with pytest.RaisesGroup(Invalid):
        is_directory("~/../foo/bar")


def test_is_directory__without_directory() -> None:
    with NamedTemporaryFile() as f, pytest.RaisesGroup(Invalid):
        is_directory(f.name)


async def test_is_directory__with_valid_str() -> None:
    with TemporaryDirectory() as directory:
        is_directory(directory)


async def test_is_directory__with_valid_path() -> None:
    with TemporaryDirectory() as directory:
        is_directory(Path(directory))
