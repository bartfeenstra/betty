from __future__ import annotations

from typing import Any

import pytest

from betty.validation import Invalid
from betty.validators.number import IsNumber, TooHigh, TooLow


class _InvalidNumber(Invalid):
    pass


def __is_number(value: Any, /) -> int:
    if not isinstance(value, int):
        raise _InvalidNumber(value, "-")
    return value


_is_number = IsNumber(__is_number)


@pytest.mark.parametrize(
    ("value", "min_", "max_"),
    [
        (123, None, None),
        (123, 123, None),
        (123, None, 123),
    ],
)
def test_is_number__with_valid_value(
    value: Any, min_: int | None, max_: int | None
) -> None:
    assert _is_number(min=min_, max=max_)(value) == value


def test_is_number__with_invalid_type() -> None:
    with pytest.raises(_InvalidNumber):
        _is_number(None)


def test_is_number__with_invalid_min() -> None:
    with pytest.raises(TooLow):
        _is_number(123, min=124)


def test_is_number__with_valid_min() -> None:
    assert _is_number(123, min=122) == 123


def test_is_number__with_invalid_max() -> None:
    with pytest.raises(TooHigh):
        _is_number(123, max=122)


def test_is_number__with_valid_max() -> None:
    assert _is_number(123, max=124) == 123
