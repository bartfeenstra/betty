from __future__ import annotations

from typing import Any

import pytest

from betty.assertions.none import assert_none
from betty.exception import HumanFacingException


def test_assert_none__with_valid_value() -> None:
    assert_none(None)


@pytest.mark.parametrize(
    "value",
    [
        True,
        False,
        123,
        "abc",
        object(),
        [],
        {},
    ],
)
def test_assert_none__with_invalid_value(value: Any) -> None:
    with pytest.raises(HumanFacingException):
        assert_none(value)
