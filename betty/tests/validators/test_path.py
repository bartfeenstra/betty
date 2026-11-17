from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory

import pytest

from betty.validation import InvalidGroup
from betty.validators.path import (
    NotADirectory,
    NotAPath,
    NotFound,
    is_directory,
    is_file,
    is_path,
)
from betty.validators.str import NotAStr


def test_is_path__with_invalid_value() -> None:
    with pytest.raises(InvalidGroup) as exc_info:
        is_path(None)
    assert isinstance(exc_info.value[0], NotAStr)
    assert isinstance(exc_info.value[1], NotAPath)


def test_is_path__with_valid_str_path() -> None:
    is_path("~/../foo/bar")


def test_is_path__with_valid_path_path() -> None:
    is_path(Path("~/../foo/bar"))


def test_is_directory__without_existing_path() -> None:
    with pytest.raises(NotFound):
        is_directory("~/../foo/bar")


def test_is_directory__without_directory() -> None:
    with NamedTemporaryFile() as f, pytest.raises(NotADirectory):
        is_directory(f.name)


async def test_is_directory__with_valid_str() -> None:
    with TemporaryDirectory() as directory:
        is_directory(directory)


async def test_is_directory__with_valid_path() -> None:
    with TemporaryDirectory() as directory:
        is_directory(Path(directory))


def test_is_file__without_existing_path() -> None:
    with pytest.raises(NotFound):
        is_file("~/../foo/bar")


def test_is_file__with_valid_str() -> None:
    with NamedTemporaryFile() as f:
        is_file(f.name)


def test_is_file__with_valid_path() -> None:
    with NamedTemporaryFile() as f:
        is_file(Path(f.name))
