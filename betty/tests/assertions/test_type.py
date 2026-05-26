from __future__ import annotations

from collections.abc import Mapping, Sequence
from types import NoneType
from typing import Any

import pytest

from betty.assertions.type import AssertTypeType, assert_type
from betty.exception import HumanFacingException


@pytest.mark.parametrize(
    ("value", "value_type"),
    [
        (True, bool),
        (False, bool),
        (123, int),
        (123.456, float),
        ({}, Mapping),
        (None, NoneType),
        ([], Sequence),
        ("", str),
    ],
)
def test_assert_type__with_valid_value(
    value: Any, value_type: type[AssertTypeType]
) -> None:
    assert_type(value_type)(value)


@pytest.mark.parametrize(
    ("value", "value_type"),
    [
        (0, bool),
        (1, bool),
        (True, int),
        (False, int),
    ],
)
def test_assert_type__with_invalid_value(
    value: Any, value_type: type[AssertTypeType]
) -> None:
    with pytest.raises(HumanFacingException):
        assert_type(value_type)(value)
