from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from betty.assertions.sequence import assert_sequence
from betty.assertions.str import assert_str
from betty.exception import HumanFacingException
from betty.indicator.operator import Index

if TYPE_CHECKING:
    from betty.functools import Pipe


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
def test_assert_sequence__with_invalid_top_level_value(value: Any) -> None:
    with pytest.raises(HumanFacingException):
        assert_sequence()(value)


def test_assert_sequence__with_invalid_item() -> None:
    with pytest.raises(HumanFacingException) as exc_info:
        assert_sequence(assert_str())([123])
    assert exc_info.value.indicators == [Index(0)]


@pytest.mark.parametrize(
    ("value", "value_assertion"),
    [
        ([], None),
        ([], assert_str()),
        (["abc"], assert_str()),
    ],
)
def test_assert_sequence__valid(
    value: Any, value_assertion: Pipe[Any, Any] | None
) -> None:
    assert_sequence(value_assertion)(value)
