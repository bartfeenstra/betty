from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from betty.operator import Index
from betty.validation import InvalidGroup
from betty.validators.always import AlwaysInvalid, is_always_invalid, is_always_valid
from betty.validators.sequence import NotASequence, is_sequence
from betty.validators.str import is_str

if TYPE_CHECKING:
    from betty.validation import Validator


@pytest.mark.parametrize(
    "value",
    [
        True,
        False,
        None,
        123,
        object(),
        {},
    ],
)
def test_is_sequence__with_invalid_value(value: Any) -> None:
    with pytest.raises(NotASequence):
        is_sequence(value)


def test_is_sequence__with_invalid_item_value() -> None:
    with pytest.raises(InvalidGroup) as exc_info:
        is_sequence(values=is_always_invalid)([123])
    assert list(exc_info.value.location) == []
    item_0_errors = exc_info.value[0]
    assert isinstance(item_0_errors, InvalidGroup)
    assert isinstance(item_0_errors[0], AlwaysInvalid)
    assert list(item_0_errors[0].location) == [Index(0)]


@pytest.mark.parametrize(
    ("value", "is_value"),
    [
        ([], is_always_valid),
        ([], is_str),
        (["abc"], is_str),
    ],
)
def test_is_sequence__valid(value: Any, is_value: Validator[Any, Any]) -> None:
    assert is_sequence(values=is_value)(value) == value
