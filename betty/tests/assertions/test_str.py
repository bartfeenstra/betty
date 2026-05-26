from __future__ import annotations

from typing import Any

import pytest

from betty.assertions.str import assert_str
from betty.exception import HumanFacingException


@pytest.mark.parametrize(
    ("value", "exact_length", "minimum_length", "maximum_length"),
    [
        ("abcde", None, None, None),
        ("abcde", 5, None, None),
        ("abcde", None, 1, None),
        ("abcde", None, 5, None),
        ("abcde", None, None, 5),
        ("abcde", None, None, 9),
    ],
)
def test_assert_str__with_valid_value(
    value: Any,
    exact_length: int | None,
    minimum_length: int | None,
    maximum_length: int | None,
) -> None:
    assert (
        assert_str(
            exact_length=exact_length,
            minimum_length=minimum_length,
            maximum_length=maximum_length,
        )(value)
        == value
    )


@pytest.mark.parametrize(
    ("value", "exact_length", "minimum_length", "maximum_length"),
    [
        (False, None, None, None),
        ("abcde", 4, None, None),
        ("abcde", 6, None, None),
        ("abcde", None, 6, None),
        ("abcde", None, None, 4),
    ],
)
def test_assert_str__with_invalid_value(
    value: Any,
    exact_length: int | None,
    minimum_length: int | None,
    maximum_length: int | None,
) -> None:
    with pytest.raises(HumanFacingException):
        assert_str(
            exact_length=exact_length,
            minimum_length=minimum_length,
            maximum_length=maximum_length,
        )(value)
