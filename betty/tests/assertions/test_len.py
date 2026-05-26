from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from betty.assertions.len import assert_len
from betty.exception import HumanFacingException

if TYPE_CHECKING:
    from collections.abc import Sized


@pytest.mark.parametrize(
    ("exact", "value"),
    [
        (0, ""),
        (3, "abc"),
        (0, []),
        (3, ["a", "b", "c"]),
        (0, {}),
        (3, {"a": 1, "b": 2, "c": 3}),
    ],
)
def test_assert_len__exact_with_valid_value(exact: int, value: Sized) -> None:
    assert_len(exact)(value)


@pytest.mark.parametrize(
    ("exact", "value"),
    [
        (1, ""),
        (4, ""),
        (4, "abc"),
        (1, []),
        (1, ["a", "b", "c"]),
        (4, ["a", "b", "c"]),
        (1, {}),
        (1, {"a": 1, "b": 2, "c": 3}),
        (4, {"a": 1, "b": 2, "c": 3}),
    ],
)
def test_assert_len__exact_with_invalid_value(exact: int, value: Sized) -> None:
    with pytest.raises(HumanFacingException):
        assert_len(exact)(value)


@pytest.mark.parametrize(
    ("minimum", "maximum", "value"),
    [
        # Minimums that match the exact length.
        (0, None, ""),
        (3, None, "abc"),
        (0, None, []),
        (3, None, ["a", "b", "c"]),
        (0, None, {}),
        (3, None, {"a": 1, "b": 2, "c": 3}),
        # Minimums that are significantly below the exact length.
        (0, None, "abc"),
        (0, None, ["a", "b", "c"]),
        (0, None, {"a": 1, "b": 2, "c": 3}),
        # Maximums that match the exact length.
        (None, 0, ""),
        (None, 3, "abc"),
        (None, 0, []),
        (None, 3, ["a", "b", "c"]),
        (None, 0, {}),
        (None, 3, {"a": 1, "b": 2, "c": 3}),
        # Maximums that are significantly above the exact length.
        (None, 9, "abc"),
        (None, 9, ["a", "b", "c"]),
        (None, 9, {"a": 1, "b": 2, "c": 3}),
    ],
)
def test_assert_len__bound_with_valid_value(
    minimum: int | None, maximum: int | None, value: Sized
) -> None:
    assert_len(minimum=minimum, maximum=maximum)(value)


@pytest.mark.parametrize(
    ("minimum", "maximum", "value"),
    [
        # Minimums.
        (1, None, ""),
        (4, None, "abc"),
        (1, None, []),
        (4, None, ["a", "b", "c"]),
        (1, None, {}),
        (4, None, {"a": 1, "b": 2, "c": 3}),
        # Maximums.
        (None, 2, "abc"),
        (None, 2, ["a", "b", "c"]),
        (None, 2, {"a": 1, "b": 2, "c": 3}),
    ],
)
def test_assert_len__bound_with_invalid_value(
    minimum: int | None, maximum: int | None, value: Sized
) -> None:
    with pytest.raises(HumanFacingException):
        assert_len(minimum=minimum, maximum=maximum)(value)
