from __future__ import annotations

from typing import Any

import pytest

from betty.validators.int import NotAnInt, is_int


def test_is_int__with_valid_value() -> None:
    assert is_int(123) == 123


@pytest.mark.parametrize(
    "value",
    [object(), True, False, 123.4],
)
def test_is_int__with_invalid_value(value: Any) -> None:
    with pytest.raises(NotAnInt):
        is_int(value)
