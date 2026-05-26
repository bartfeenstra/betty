from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from betty.assertions.record import Field, assert_record
from betty.assertions.str import assert_str
from betty.exception import HumanFacingException
from betty.indicator.selector import Key

if TYPE_CHECKING:
    from collections.abc import Mapping


def test_assert_record__with_unknown_key_should_error() -> None:
    with pytest.raises(HumanFacingException) as exc_info:
        assert_record()({"unknown-key": True})
    assert exc_info.value.indicators == [Key("unknown-key")]


def test_assert_record__with_optional_fields_without_items() -> None:
    expected: Mapping[str, Any] = {}
    actual = assert_record(Field("hello", assert_str(), optional=True))({})
    assert actual == expected


def test_assert_record__with_optional_fields_with_items() -> None:
    expected = {
        "hello": "WORLD!",
    }
    actual = assert_record(
        Field("hello", assert_str().pipe(lambda x: x.upper()), optional=True)
    )({"hello": "World!"})
    assert actual == expected


def test_assert_record__with_required_fields_without_items() -> None:
    with pytest.raises(HumanFacingException):
        assert_record(Field("hello", assert_str()))({})


def test_assert_record__with_required_fields_with_items() -> None:
    expected = {
        "hello": "WORLD!",
    }
    actual = assert_record(Field("hello", assert_str().pipe(lambda x: x.upper())))({
        "hello": "World!",
    })
    assert actual == expected


def test_assert_record__with_as_name() -> None:
    expected = {
        "as_hello": "World!",
    }
    actual = assert_record(Field("hello", None, as_name="as_hello"))({
        "hello": "World!",
    })
    assert actual == expected
