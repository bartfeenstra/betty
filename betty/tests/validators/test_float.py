from __future__ import annotations

from typing import Any

import pytest

from betty.validators.float import NotAFloat, is_float


def test_is_float__with_valid_value() -> None:
    assert is_float(123) == 123
    assert is_float(123.4) == 123.4


@pytest.mark.parametrize(
    "value",
    [
        object(),
        True,
        False,
    ],
)
def test_is_float__with_invalid_value(value: Any) -> None:
    with pytest.raises(NotAFloat):
        is_float(value)
