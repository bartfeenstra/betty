from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from betty.assertions.mapping import assert_mapping
from betty.assertions.str import assert_str
from betty.exception import HumanFacingException
from betty.indicator.operator import Key

if TYPE_CHECKING:
    from betty.functools import Pipe


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
def test_assert_mapping__with_invalid_top_level_value(value: Any) -> None:
    with pytest.raises(HumanFacingException):
        assert_mapping()(value)


def test_assert_mapping__with_invalid_item_value() -> None:
    with pytest.raises(HumanFacingException) as exc_info:
        assert_mapping(assert_str())({"abc": 123})
    assert exc_info.value.indicators == [Key("abc")]


def test_assert_mapping__with_invalid_item_key() -> None:
    with pytest.raises(HumanFacingException) as exc_info:
        assert_mapping(None, assert_str())({123: "abc"})
    assert exc_info.value.indicators == [Key("123")]


@pytest.mark.parametrize(
    ("value", "value_assertion", "key_assertion"),
    [
        ({}, None, None),
        ({}, assert_str(), None),
        ({}, None, assert_str()),
        ({123: "abc"}, assert_str(), None),
        ({"abc": 123}, None, assert_str()),
    ],
)
def test_assert_mapping__valid(
    value: Any,
    value_assertion: Pipe[Any, Any] | None,
    key_assertion: Pipe[Any, Any] | None,
) -> None:
    assert_mapping(value_assertion, key_assertion)(value)
