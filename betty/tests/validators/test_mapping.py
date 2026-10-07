from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from betty.operator import Key
from betty.validation import InvalidGroup
from betty.validators.always import AlwaysInvalid, is_always_invalid, is_always_valid
from betty.validators.mapping import NotAMapping, is_mapping
from betty.validators.str import is_str

if TYPE_CHECKING:
    from betty.validation import Validator


@pytest.mark.parametrize(
    "value",
    [
        True,
        False,
        None,
        "abc",
        123,
        object(),
        [],
    ],
)
def test_is_mapping__with_invalid_value(value: Any) -> None:
    with pytest.raises(NotAMapping):
        is_mapping()(value)


def test_is_mapping__with_invalid_item_value() -> None:
    with pytest.raises(InvalidGroup) as exc_info:
        is_mapping(values=is_always_invalid)({"abc": 123})
    assert list(exc_info.value.location) == []
    item_0_errors = exc_info.value[0]
    assert isinstance(item_0_errors, InvalidGroup)
    assert isinstance(item_0_errors[0], AlwaysInvalid)
    assert list(item_0_errors[0].location) == [Key("abc")]


def test_is_mapping__with_invalid_item_key() -> None:
    with pytest.raises(InvalidGroup) as exc_info:
        is_mapping(keys=is_always_invalid)({123: "abc"})
    assert list(exc_info.value[0].location) == []


@pytest.mark.parametrize(
    ("value", "keys", "values"),
    [
        ({}, is_always_valid, is_always_valid),
        ({}, is_always_valid, is_str),
        ({}, is_str, is_always_valid),
        ({123: "abc"}, is_always_valid, is_str),
        ({"abc": 123}, is_str, is_always_valid),
    ],
)
def test_is_mapping__valid(
    value: Any, keys: Validator[Any, Any], values: Validator[Any, Any]
) -> None:
    assert is_mapping(keys=keys, values=values)(value) == value
