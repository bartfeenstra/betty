from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from betty.operator import Key
from betty.validation import InvalidGroup
from betty.validators.record import Field, MissingField, UnknownField, is_record
from betty.validators.str import is_str

if TYPE_CHECKING:
    from collections.abc import Mapping


def test_is_record__with_unknown_key_should_error() -> None:
    with pytest.raises(InvalidGroup) as exc_info:
        is_record()({"unknown-key": True})
    assert list(exc_info.value.location) == []
    assert isinstance(exc_info.value[0], UnknownField)
    assert list(exc_info.value[0].location) == [Key("unknown-key")]


def test_is_record__with_optional_fields_without_items() -> None:
    expected: Mapping[str, Any] = {}
    actual = is_record(Field("hello", is_str, optional=True))({})
    assert actual == expected


def test_is_record__with_optional_fields_with_items() -> None:
    expected = {
        "hello": "WORLD!",
    }
    actual = is_record(Field("hello", is_str | (lambda x: x.upper()), optional=True))({
        "hello": "World!"
    })
    assert actual == expected


def test_is_record__with_required_fields_without_items() -> None:
    with pytest.raises(InvalidGroup) as exc_info:
        is_record(Field("hello", is_str))({})
    assert isinstance(exc_info.value[0], MissingField)
    assert list(exc_info.value[0].location) == [Key("hello")]


def test_is_record__with_required_fields_with_items() -> None:
    expected = {
        "hello": "WORLD!",
    }
    actual = is_record(Field("hello", is_str | (lambda x: x.upper())))({
        "hello": "World!",
    })
    assert actual == expected
