from __future__ import annotations

from typing import Any

import pytest

from betty.validation import Invalid
from betty.validators.int import is_int


@pytest.mark.parametrize(
    ("value", "min", "max"),
    [
        (123, None, None),
        (123, 123, None),
        (123, None, 123),
    ],
)
def test_is_int__with_valid_value(
    value: Any,
    min: int | None,  # noqa: A002
    max: int | None,  # noqa: A002
) -> None:
    is_int(min=min, max=max)(value)


@pytest.mark.parametrize(
    ("value", "min", "max"),
    [
        (1.23, None, None),
        (123, 124, None),
        (123, None, 122),
    ],
)
def test_is_int__with_invalid_value(
    value: Any,
    min: int | None,  # noqa: A002
    max: int | None,  # noqa: A002
) -> None:
    with pytest.RaisesGroup(Invalid):
        is_int(min=min, max=max)(False)
