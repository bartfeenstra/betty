from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory

import pytest

from betty.assertions.directory import assert_directory
from betty.exception import HumanFacingException


def test_assert_directory__without_existing_path() -> None:
    with pytest.raises(HumanFacingException):
        assert_directory()("~/../foo/bar")


def test_assert_directory__without_directory() -> None:
    with NamedTemporaryFile() as f, pytest.raises(HumanFacingException):
        assert_directory()(f.name)


async def test_assert_directory__with_valid_str() -> None:
    with TemporaryDirectory() as directory:
        assert_directory()(directory)


async def test_assert_directory__with_valid_path() -> None:
    with TemporaryDirectory() as directory:
        assert_directory()(Path(directory))
