from __future__ import annotations

from enum import Enum
from typing import Any

import pytest

from betty.assertions.enum import assert_enum
from betty.exception import HumanFacingException


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
def test_assert_enum(expected: _Enum, value: Any) -> None:
    assert assert_enum(_Enum)(value) == expected


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
def test_assert_enum__with_invalid_value(value: Any) -> None:
    with pytest.raises(HumanFacingException):
        assert_enum(_Enum)(value)
