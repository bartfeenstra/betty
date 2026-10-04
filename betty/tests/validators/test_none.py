from __future__ import annotations

from typing import Any

import pytest

from betty.validation import Invalid
from betty.validators.none import is_none


def test_is_none__with_valid_value() -> None:
    is_none(None)


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
def test_is_none__with_invalid_value(value: Any) -> None:
    with pytest.RaisesGroup(Invalid):
        is_none(value)
