from __future__ import annotations

from typing import Any

import pytest

from betty.validation import Invalid
from betty.validators.float import is_float


@pytest.mark.parametrize(
    ("value", "min", "max"),
    [
        (123, None, None),
        (123, 123, None),
        (123, None, 123),
    ],
)
def test_is_number__with_valid_value(
    value: Any,
    min: float | None,  # noqa: A002
    max: float | None,  # noqa: A002
) -> None:
    is_float(min=min, max=max)(value)


@pytest.mark.parametrize(
    ("value", "min", "max"),
    [
        (object(), None, None),
        (123, 124, None),
        (1.23, 1.24, None),
        (123, None, 122),
        (1.23, None, 1.22),
    ],
)
def test_is_number__with_invalid_value(
    value: Any,
    min: float | None,  # noqa: A002
    max: float | None,  # noqa: A002
) -> None:
    with pytest.RaisesGroup(Invalid):
        is_float(min=min, max=max)(False)
