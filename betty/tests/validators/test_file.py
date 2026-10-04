from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile

import pytest

from betty.validation import Invalid
from betty.validators.file import is_file


def test_is_file__without_existing_file() -> None:
    with pytest.RaisesGroup(Invalid):
        is_file("~/../foo/bar")


def test_is_file__with_valid_str() -> None:
    with NamedTemporaryFile() as f:
        is_file(f.name)


def test_is_file__with_valid_path() -> None:
    with NamedTemporaryFile() as f:
        is_file(Path(f.name))
