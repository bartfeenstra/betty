from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile

import pytest

from betty.assertions.file import assert_file
from betty.exception import HumanFacingException


def test_assert_file__without_existing_file() -> None:
    with pytest.raises(HumanFacingException):
        assert_file()("~/../foo/bar")


def test_assert_file__with_valid_str() -> None:
    with NamedTemporaryFile() as f:
        assert_file()(f.name)


def test_assert_file__with_valid_path() -> None:
    with NamedTemporaryFile() as f:
        assert_file()(Path(f.name))
