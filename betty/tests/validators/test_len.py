from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from betty.validation import Invalid
from betty.validators.len import is_len

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
def test_is_len__exact_with_valid_value(exact: int, value: Sized) -> None:
    is_len(exact)(value)


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
def test_is_len__exact_with_invalid_value(exact: int, value: Sized) -> None:
    with pytest.RaisesGroup(Invalid):
        is_len(exact)(value)


@pytest.mark.parametrize(
    ("min", "max", "value"),
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
def test_is_len__bound_with_valid_value(
    min: int | None,  # noqa: A002
    max: int | None,  # noqa: A002
    value: Sized,
) -> None:
    is_len(min=min, max=max)(value)


@pytest.mark.parametrize(
    ("min", "max", "value"),
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
def test_is_len__bound_with_invalid_value(
    min: int | None,  # noqa: A002
    max: int | None,  # noqa: A002
    value: Sized,
) -> None:
    with pytest.RaisesGroup(Invalid):
        is_len(min=min, max=max)(value)
