from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from betty.locator.operator import Index
from betty.validation import Invalid
from betty.validators.sequence import is_sequence
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
def test_is_sequence__with_invalid_top_level_value(value: Any) -> None:
    with pytest.RaisesGroup(Invalid):
        is_sequence(value)


def test_is_sequence__with_invalid_item() -> None:
    with pytest.RaisesGroup(Invalid) as exc_info:
        is_sequence(values=is_str)([123])
    assert exc_info.value.indicators == [Index(0)]


@pytest.mark.parametrize(
    ("value", "is_value"),
    [
        ([], None),
        ([], is_str),
        (["abc"], is_str),
    ],
)
def test_is_sequence__valid(value: Any, is_value: Validator[Any, Any] | None) -> None:
    is_sequence(values=is_value)(value)
