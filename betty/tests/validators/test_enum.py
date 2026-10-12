from __future__ import annotations

from enum import Enum
from typing import Any

import pytest

from betty.validators.enum import UnknownOption, is_enum


class _Enum(Enum):
    STRING = "string"
    INT = 123


@pytest.mark.parametrize(
    ("expected", "value"),
    [
        (_Enum.STRING, "string"),
        (_Enum.INT, 123),
    ],
)
def test_is_enum(expected: _Enum, value: Any) -> None:
    assert is_enum(_Enum)(value) == expected


@pytest.mark.parametrize(
    "value",
    [
        True,
        False,
        456,
        "",
        object(),
        [],
        {},
    ],
)
def test_is_enum__with_invalid_value(value: Any) -> None:
    with pytest.raises(UnknownOption):
        is_enum(_Enum)(value)
