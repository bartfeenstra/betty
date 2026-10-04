from __future__ import annotations

from typing import Any

import pytest

from betty.validation import Invalid
from betty.validators.str import is_str


@pytest.mark.parametrize(
    ("value", "len_", "min_len", "max_len"),
    [
        ("abcde", None, None, None),
        ("abcde", 5, None, None),
        ("abcde", None, 1, None),
        ("abcde", None, 5, None),
        ("abcde", None, None, 5),
        ("abcde", None, None, 9),
    ],
)
def test_is_str__with_valid_value(
    value: Any,
    len_: int | None,
    min_len: int | None,
    max_len: int | None,
) -> None:
    assert (
        is_str(
            len=len_,
            min_len=min_len,
            max_len=max_len,
        )(value)
        == value
    )


@pytest.mark.parametrize(
    ("value", "len_", "min_len", "max_len"),
    [
        (False, None, None, None),
        ("abcde", 4, None, None),
        ("abcde", 6, None, None),
        ("abcde", None, 6, None),
        ("abcde", None, None, 4),
    ],
)
def test_is_str__with_invalid_value(
    value: Any,
    len_: int | None,
    min_len: int | None,
    max_len: int | None,
) -> None:
    with pytest.RaisesGroup(Invalid):
        is_str(
            len=len_,
            min_len=min_len,
            max_len=max_len,
        )(value)
