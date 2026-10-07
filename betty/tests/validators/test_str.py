from __future__ import annotations

from typing import Any

import pytest

from betty.validators.str import NotAStr, is_str


def test_is_str__with_valid_value() -> None:
    assert is_str("") == ""
    assert is_str("aBc") == "aBc"


@pytest.mark.parametrize(
    "value",
    [123, True, [], object()],
)
def test_is_str__with_invalid_value(value: Any) -> None:
    with pytest.raises(NotAStr):
        is_str(value)
