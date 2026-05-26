from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from betty.assertions.if_else import assert_if_else
from betty.exception import HumanFacingException
from betty.tests.assertions.test___init__ import _always_invalid, _always_valid

if TYPE_CHECKING:
    from betty.functools import Pipe


@pytest.mark.parametrize(
    ("if_assertion", "else_assertion", "value"),
    [
        (_always_valid, _always_valid, 123),
        (_always_valid, _always_invalid, 123),
        (_always_invalid, _always_valid, 123),
    ],
)
def test_assert_if_else__with_valid_assertion(
    if_assertion: Pipe[Any, bool],
    else_assertion: Pipe[Any, bool],
    value: int,
) -> None:
    assert assert_if_else(if_assertion, else_assertion)(value) == value


def test_assert_if_else__with_invalid_assertion() -> None:
    with pytest.raises(HumanFacingException):
        assert_if_else(_always_invalid, _always_invalid)(123)
