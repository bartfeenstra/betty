from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from betty.locator.operator import Key
from betty.validation import Invalid
from betty.validators.mapping import is_mapping
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
def test_is_mapping__with_invalid_top_level_value(value: Any) -> None:
    with pytest.RaisesGroup(Invalid):
        is_mapping()(value)


def test_is_mapping__with_invalid_item_value() -> None:
    with pytest.RaisesGroup(Invalid) as exc_info:
        is_mapping(values=is_str)({"abc": 123})
    assert exc_info.value.indicators == [Key("abc")]


def test_is_mapping__with_invalid_item_key() -> None:
    with pytest.RaisesGroup(Invalid) as exc_info:
        is_mapping(keys=is_str)({123: "abc"})
    assert exc_info.value.indicators == [Key("123")]


@pytest.mark.parametrize(
    ("value", "keys", "values"),
    [
        ({}, None, None),
        ({}, None, is_str),
        ({}, is_str, None),
        ({123: "abc"}, None, is_str),
        ({"abc": 123}, is_str, None),
    ],
)
def test_is_mapping__valid(
    value: Any, values: Validator[Any, Any] | None, keys: Validator[Any, Any] | None
) -> None:
    is_mapping(keys=keys, values=values)(value)
